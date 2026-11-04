"""Build EVIDENCE_INDEX.jsonl, FILE_MANIFEST_SHA256.csv and SNAPSHOT_METADATA.json for the snapshot.

Usage: python build_manifest.py <snapshot_dir>
"""
import csv,hashlib,json,os,sys,time
S=sys.argv[1]
GITHUB_EXCLUDED=('02_EXECUTION/training_logs/',)
DESC=[('00_README/','Orientation documents'),('01_PROTOCOL/frozen_config','Frozen study configuration'),('01_PROTOCOL/protocol_lock','Protocol lock (hashes of config, seeds, source, datasets, runtime ABI)'),
 ('01_PROTOCOL/seed_manifest','Seed manifest'),('01_PROTOCOL/study_matrix','Expanded 226-run design'),('01_PROTOCOL/source_identity','Source identity, environment lock, stage state'),
 ('02_EXECUTION/sqlite_snapshot','Transactionally consistent SQLite backup of the queue'),('02_EXECUTION/job_inventory','Per-job inventory exported from the snapshot'),
 ('02_EXECUTION/training_receipts','Training receipts (41 completed trajectories)'),('02_EXECUTION/training_logs','Per-step training logs'),('02_EXECUTION/checkpoint_manifest','Checkpoint file hashes (weights not uploaded)'),
 ('02_EXECUTION/failure_records','Failure trace, lifecycle log, G0/doctor receipts, stage reports'),('03_SCIENTIFIC_DATA/raw_measurement_records','Full measurement receipts and probe artifacts, sharded'),
 ('03_SCIENTIFIC_DATA/utility','Flat utility table'),('03_SCIENTIFIC_DATA/structure','Structure records'),('03_SCIENTIFIC_DATA/mechanism','Mechanism records'),
 ('03_SCIENTIFIC_DATA/prediction','Derived predictor feature table (not a formal predictor dataset)'),('03_SCIENTIFIC_DATA/numerical_eligibility','Numerical eligibility and solver residual tables'),
 ('04_NUMERICAL_AUDIT/fp32_vs_fp64','FP32 vs FP64 audit: protocol, script, rows, report'),('04_NUMERICAL_AUDIT/false_valid_cases','False-valid rows and gradient errors'),
 ('04_NUMERICAL_AUDIT/cg_preconditioner','CG/preconditioner diagnostics'),('04_NUMERICAL_AUDIT/residual_corrections','Relative-residual error and correction'),('04_NUMERICAL_AUDIT/reproducibility','Thread dependence and coarse/fine redundancy evidence'),
 ('05_V21_QUALIFICATION/solver_variants','v2.1 harnesses and experimental diff'),('05_V21_QUALIFICATION/dln_comparison','DLN solver variant comparison'),('05_V21_QUALIFICATION/mlp_resnet_transformer','Non-DLN solver comparison on frozen preflight states'),
 ('05_V21_QUALIFICATION/go_no_go','v2.1 GO/NO-GO report'),('06_ANALYSIS/existing_statistics','Descriptive coverage tables'),('06_ANALYSIS/existing_reports','Stage evidence and takeover reports'),
 ('06_ANALYSIS/analysis_scripts','Scripts that produced the exports in this package'),('07_SOURCE/executed_source','Executed v2 source tree'),('07_SOURCE/local_changes','Uncommitted edits to the executed source'),
 ('07_SOURCE/git_metadata','Git identity of the executed source'),('07_SOURCE/tests','Package tests'),('08_AUDIT_LEDGER/','Claim ledger and limitations'),('09_MANIFEST/','Manifest and exclusions')]
def desc(p):
    for k,v in DESC:
        if p.startswith(k):return v
    return 'Package file'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def nrec(p):
    if p.endswith('.jsonl'):return sum(1 for _ in open(p,'rb'))
    if p.endswith('.csv'):return max(0,sum(1 for _ in open(p,'rb'))-1)
    return None
files=[]
for dp,dn,fn in os.walk(S):
    dn[:]=[d for d in dn if d!='__pycache__']
    for f in fn:
        p=os.path.relpath(os.path.join(dp,f),S).replace(os.sep,'/')
        if p.endswith('.pyc') or p=='09_MANIFEST/FILE_MANIFEST_SHA256.csv' or p=='09_MANIFEST/SNAPSHOT_METADATA.json' or p=='08_AUDIT_LEDGER/EVIDENCE_INDEX.jsonl':continue
        files.append(p)
files.sort()
claims={}
for l in open(f'{S}/08_AUDIT_LEDGER/CLAIM_LEDGER.jsonl',encoding='utf-8'):
    c=json.loads(l)
    for q in c['evidence_ids']+c['source_paths']:claims.setdefault(q,[]).append(c['claim_id'])
with open(f'{S}/08_AUDIT_LEDGER/EVIDENCE_INDEX.jsonl','w',encoding='utf-8',newline='\n') as out:
    for p in files:
        if p.startswith('09_MANIFEST/'):continue
        ids=sorted({c for k,v in claims.items() if p==k or (k.endswith('/') and p.startswith(k)) for c in v})
        out.write(json.dumps({'evidence_id':'E:'+p,'path':p,'sha256':sha(f'{S}/{p}'),'bytes':os.path.getsize(f'{S}/{p}'),'records':nrec(f'{S}/{p}'),'description':desc(p),
            'on_github':not p.startswith(GITHUB_EXCLUDED),'claims':ids},sort_keys=True)+'\n')
files2=files+['08_AUDIT_LEDGER/EVIDENCE_INDEX.jsonl'];files2.sort()
tot=0;gh=0;ghb=0
with open(f'{S}/09_MANIFEST/FILE_MANIFEST_SHA256.csv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['path','bytes','sha256','on_github'])
    for p in files2:
        b=os.path.getsize(f'{S}/{p}');on=not p.startswith(GITHUB_EXCLUDED);tot+=b;gh+=on;ghb+=b*on
        w.writerow([p,b,sha(f'{S}/{p}'),'yes' if on else 'no'])
meta=json.load(open(f'{S}/02_EXECUTION/sqlite_snapshot/snapshot_info.json'))
inv=[json.loads(l) for l in open(f'{S}/02_EXECUTION/job_inventory/job_inventory.jsonl',encoding='utf-8')]
json.dump({'snapshot_dir_name':os.path.basename(S.rstrip('/')),'snapshot_queue_time':meta['iso_start'],'queue_max_updated_epoch':meta['max_updated_in_snapshot'],'protocol_sha':'b580695c152f85ac5ab79b3d070e5f660c28118d2cbe4a4c45c2c057b8a0c5c3',
 'executed_commit':'12c240e1a22445b6fd6a50dfbe8552815de1fb71','source_has_uncommitted_local_edits':True,'sqlite_snapshot_sha256':open(f'{S}/02_EXECUTION/sqlite_snapshot/run_status_snapshot.sqlite.sha256').read().split()[0],
 'queue_counts':{f'{k}/{s}':sum(1 for r in inv if r['kind']==k and r['state']==s) for k in ('train','measure') for s in sorted({r['state'] for r in inv if r['kind']==k})},
 'file_count':len(files2),'bytes_total':tot,'files_on_github':gh,'bytes_on_github':ghb,'manifest_sha256':sha(f'{S}/09_MANIFEST/FILE_MANIFEST_SHA256.csv'),
 'evidence_index_sha256':sha(f'{S}/08_AUDIT_LEDGER/EVIDENCE_INDEX.jsonl'),'manifest_built_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')},open(f'{S}/09_MANIFEST/SNAPSHOT_METADATA.json','w'),indent=1)
print(len(files2),tot,gh,ghb)
