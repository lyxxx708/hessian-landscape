"""Export raw measurement shards and flat tables from verified receipts.

Source receipts are those committed in the snapshot (job_inventory.jsonl), verified by SHA-256 against the live run
root read-only. Derived predictor features use the frozen features() function and are NOT the formal predictor dataset.

Usage: python -B -I export_science.py <snapshot_dir> <run_root> <frozen_source_dir>
"""
import csv,hashlib,json,os,sys
snap,root,frozen=sys.argv[1:4]
sys.path.insert(0,frozen)
from genesis_gpu.science.predictor import features
LIMIT=8*1024*1024
inv=[json.loads(l) for l in open(f'{snap}/02_EXECUTION/job_inventory/job_inventory.jsonl',encoding='utf-8')]
def sha(b):return hashlib.sha256(b).hexdigest()
def scalars(d,prefix=''):
    return {prefix+k:v for k,v in (d or {}).items() if not isinstance(v,(dict,list))}
class Shards:
    def __init__(self,dirn,stem):
        self.d,self.stem,self.i,self.f,self.n,self.size,self.index=dirn,stem,0,None,0,0,[]
    def write(self,rec_id,obj):
        line=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
        if self.f is None or self.size+len(line)>LIMIT:
            self.close();self.i+=1;self.name=f'{self.stem}_{self.i:03d}.jsonl';self.f=open(f'{self.d}/{self.name}','wb');self.size=0;self.n=0;self.ids=[]
        self.f.write(line);self.size+=len(line);self.n+=1;self.ids.append(rec_id)
    def close(self):
        if self.f:
            self.f.close();p=f'{self.d}/{self.name}'
            self.index.append({'shard':self.name,'records':self.n,'bytes':os.path.getsize(p),'sha256':sha(open(p,'rb').read()),'first_id':self.ids[0],'last_id':self.ids[-1]});self.f=None
D=f'{snap}/03_SCIENTIFIC_DATA'
rc_sh=Shards(f'{D}/raw_measurement_records','receipts');pr_sh=Shards(f'{D}/raw_measurement_records','probe_artifacts')
util_rows=[];elig_rows=[];feat_rows=[];bad=[];binary=[]
struct=open(f'{D}/structure/structure_records.jsonl','w',encoding='utf-8',newline='\n');mech=open(f'{D}/mechanism/mechanism_records.jsonl','w',encoding='utf-8',newline='\n')
ms=[r for r in inv if r['kind']=='measure' and r['receipt_path']]
ms.sort(key=lambda r:(r['family'],r['setting_id'],r['seed_index'],r['checkpoint_index'],r['gamma'],r['schema']))
for r in ms:
    raw=open(os.path.join(root,r['receipt_path']),'rb').read()
    if sha(raw)!=r['receipt_sha256']:
        bad.append(r['job_id']);continue
    rc=json.loads(raw)
    ids={k:r[k] for k in ('job_id','ordinal','family','setting_id','run_id','seed_index','seed','checkpoint_index','gamma','schema','tier','state')}
    rc_sh.write(r['job_id'],{**ids,'receipt_path':r['receipt_path'],'receipt_sha256':r['receipt_sha256'],'receipt':rc})
    for a in rc.get('artifacts',[]):
        ab=open(os.path.join(root,a['path']),'rb').read()
        if sha(ab)!=a['sha256']:
            bad.append(a['path']);continue
        if not a['path'].endswith('.json'):
            binary.append({**ids,'artifact_path':a['path'],'bytes':len(ab),'sha256':a['sha256'],'status':'LOCAL_EVIDENCE_REQUIRED (binary, not embedded)'});continue
        pr_sh.write(r['job_id'],{**ids,'artifact_path':a['path'],'artifact_sha256':a['sha256'],'artifact':json.loads(ab)})
    u=rc.get('utility') or {}
    row={**ids,'receipt_status':rc['status'],'lambda_absolute':rc['lambda_absolute'],'wall_seconds':rc['wall_seconds'],'total_GGN_matvecs':rc['total_GGN_matvecs'],
         'spectral_scale':rc['spectral_scale']['value'],'gradient_norm_state':rc['state_observations'].get('gradient_norm'),'loss':rc['state_observations'].get('loss'),
         'validation_loss':rc['state_observations'].get('validation_loss'),**scalars(u)}
    for sub in ('full_solve','tight_full_solve','matched_cg','short_cg','preconditioner','block_energy_proxy'):
        row.update(scalars(u.get(sub),sub+'.'))
    bs=u.get('block_solves') or []
    if bs:
        row['block_solves.n']=len(bs);row['block_solves.max_iterations']=max(s.get('iterations',0) for s in bs)
        row['block_solves.max_true_residual_relative']=max((s.get('true_residual') or 0) for s in bs)
    util_rows.append(row)
    fs=u.get('full_solve') or {};ts=u.get('tight_full_solve') or {}
    elig_rows.append({**ids,'receipt_status':rc['status'],'utility_status':u.get('status'),'reason':u.get('reason'),'task_status':u.get('task_status'),'delta':u.get('delta'),
        'delta_stability':u.get('delta_stability'),'full_solve.status':fs.get('status'),'full_solve.iterations':fs.get('iterations'),
        'full_solve.true_residual_relative':fs.get('true_residual'),'full_solve.absolute_residual':fs.get('absolute_residual'),
        'tight_status':ts.get('status'),'tight_iterations':ts.get('iterations'),'tight_rtol':u.get('tight_rtol'),
        'structure_status':(rc.get('structure') or {}).get('status'),'structure_reason':(rc.get('structure') or {}).get('reason')})
    if rc.get('structure'):
        struct.write(json.dumps({**ids,'structure':rc['structure']},sort_keys=True)+'\n')
    if rc.get('mechanism'):
        mech.write(json.dumps({**ids,'mechanism':rc['mechanism']},sort_keys=True)+'\n')
    if r['schema']=='coarse':
        f=features(rc)
        names=['log10_gamma','log10_grad','layer_scale_cv','log10_1_plus_scale_over_lambda','short_gain_over_g2','cheap_rho','matched_gain_over_g2','offdiag_fraction_proxy']
        feat_rows.append({**ids,'enters_formal_predictor_if_s1_complete':r['checkpoint_index']!=0 and u.get('status')=='NUMERIC_VALID','target_delta':u.get('delta'),
            'features_available':f is not None,**({} if f is None else dict(zip(names,f)))})
rc_sh.close();pr_sh.close();struct.close();mech.close()
def csvw(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
csvw(f'{D}/utility/utility_rows.csv',util_rows);csvw(f'{D}/numerical_eligibility/eligibility_rows.csv',elig_rows)
csvw(f'{D}/prediction/DERIVED_predictor_feature_table.csv',feat_rows)
json.dump({'receipt_shards':rc_sh.index,'probe_artifact_shards':pr_sh.index,'binary_artifacts_not_embedded':binary,'unverified_or_bad':bad},open(f'{D}/raw_measurement_records/shard_index.json','w'),indent=1)
print('binary',len(binary),sum(b['bytes'] for b in binary));print('measure receipts',len(util_rows),'receipt shards',len(rc_sh.index),'probe shards',len(pr_sh.index),'bad',bad)
