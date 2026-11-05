import json,csv,hashlib,shutil,subprocess,sys,time,platform,statistics as st
from pathlib import Path
TS=sys.argv[1]
O=Path(r'E:\GENESIS\runs\genesis_next_v2');W=Path(r'E:\GENESIS\worktrees\genesis-next-v2')
P=Path(rf'E:\GENESIS\handoff\GENESIS_NEXT_v2_AUDIT_{TS}')
assert not P.exists();P.mkdir(parents=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cp(src,dst):
    dst=P/dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
# A. results (unchanged copies)
for n in ['SCIENTIFIC_RESULTS.csv','CG_COST_COMPARISON.csv','STRUCTURE_MECHANISM_RESULTS.jsonl','NUMERICAL_ERROR_AUDIT.jsonl','NUMERICAL_QUALIFICATION.csv','EXPERIMENT_INVENTORY.csv','FAILURES_AND_CENSORING.csv','SEED_SUMMARY.csv','STRUCTURE_UTILITY_ASSOCIATIONS.csv','COVERAGE.json','NEXT_V2_EXECUTION_STATE.json','NEXT_V2_PROTOCOL_LOCK.json','FOLLOWUP_LOCK.json','SCIENTIFIC_VERDICT.md','REPRODUCIBILITY.md','RESOURCE_ACCOUNTING.md','NEXT_ACTIONS.md','DRIVER.json','DRIVER_PID.txt']:
    cp(O/n,f'original_report/{n}' if n.endswith('.md') or n.endswith('.json') and n.startswith('NEXT') else f'results/{n}')
cp(Path(r'E:\GENESIS\evidence\genesis_next_v2\FINAL_HANDOFF.md'),'original_report/FINAL_HANDOFF.md')
for p in (O/'results').glob('*.json'):cp(p,f'results/per_state/{p.name}')
for p in (O/'logs').glob('*'):cp(p,f'logs/{p.name}')
for p in (O/'invocations').glob('*'):cp(p,f'logs/invocations/{p.name}')
for p in (O/'_superseded_freeze1').rglob('*'):
    if p.is_file():cp(p,f'superseded_freeze1/{p.relative_to(O/"_superseded_freeze1").as_posix()}')
for d in ('_dev_pilot','_dev_pilot2'):
    for p in (O/d).rglob('*'):
        if p.is_file() and p.suffix in ('.json',):cp(p,f'dev_pilots_not_in_tables/{d}/{p.relative_to(O/d).as_posix()}')
# B. code
for p in W.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:cp(p,f'source_genesis_next_v2/{p.relative_to(W).as_posix()}')
for n in ('patch_v2.py','patch2.py','mkmanifest.py','mklock.py','pilot.py','finalize.py','view.py','view2.py','v3.py','manifest.py','build_audit.py'):
    if (O/'tools'/n).exists():cp(O/'tools'/n,f'run_tools/{n}')
v1=Path(r'E:\GENESIS\handoff\GENESIS_NEXT_v1_FINAL')
for n in ('V1_FINAL_STATE.md','V1_UNFINISHED_WORK.md','V1_EVIDENCE_MANIFEST.json'):cp(v1/n,f'v1_inheritance/{n}')
env=subprocess.run([r'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe','-m','pip','freeze'],capture_output=True,text=True).stdout
(P/'environment').mkdir();(P/'environment/pip_freeze.txt').write_text(env)
(P/'environment/platform.txt').write_text(f'{platform.platform()}\npython(venv)=3.11.x per venv\nOMP_NUM_THREADS=2 required\nsource v2 audit commit 629032110fa51affc7f4e96cdb75f0c40070a9fe\n')
t=subprocess.run([r'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe','-B','-m','unittest','discover','-s','tests','-v'],cwd=W,capture_output=True,text=True,env={**__import__('os').environ,'OMP_NUM_THREADS':'2','PYTHONPATH':str(W),'PYTHONDONTWRITEBYTECODE':'1'})
(P/'tests').mkdir();(P/'tests/test_run_at_audit.log').write_text(t.stdout+t.stderr)
# provenance SHA list + condition evidence
lock=json.loads((O/'FOLLOWUP_LOCK.json').read_text())
res={p.stem:json.loads(p.read_text()) for p in (O/'results').glob('*.json')}
prov=[];ev=[];den=[]
sci={(r['state_id'],float(r['gamma'])):r for r in csv.DictReader((O/'SCIENTIFIC_RESULTS.csv').open())}
inv=list(csv.DictReader((O/'EXPERIMENT_INVENTORY.csv').open()))
bystate={s['state_id']:s for s in lock['plan']['states']}
for s in lock['plan']['states']:
    sid=s['state_id'];r=res.get(sid);run=s['run']
    d={'state_id':sid,'setting_id':run['setting_id'],'family':run['model']['family'],'seed_index':run['seed_index'],'seed':str(run['seed']),'checkpoint':s['checkpoint_index'],'run_id':run['run_id'],'status':'EXECUTED' if r else 'SOURCE_NOT_READY','reason':None if r else 'no COMPLETE v2 S1 training receipt at run time; no replacement'}
    den.append(d)
    if r:
        pv=r['provenance'];prov.append({'state_id':sid,'run_id':pv['run_id'],'checkpoint_step':pv['checkpoint_step'],'checkpoint_integrity_sha':pv['checkpoint_integrity_sha'],'model_sha':pv['model_sha'],'data_sha':pv['data_sha'],'training_receipt_sha256':r['training_receipt_sha256'],'batch_seed':pv['batch_seed'],'operator_identity':json.dumps(pv['operator_identity'],sort_keys=True)[:200],'result_file_sha256':sha(O/'results'/f'{sid}.json')})
for name,rows in (('state_denominator_80.csv',den),('checkpoint_and_data_sha_manifest.csv',prov)):
    (P/'derived').mkdir(exist_ok=True)
    with (P/'derived'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for row in inv:
    sid=row['state_id'];g=float(row['gamma']);rec={'state_id':sid,'setting_id':row['setting_id'],'family':row['family'],'seed_index':int(row['seed_index']),'seed':str(bystate[sid]['run']['seed']),'checkpoint':int(row['checkpoint']),'gamma':g,'ledger_status':row['status']}
    if row['status']=='NUMERIC_VALID':
        x=sci[(sid,g)];rf=f'results/per_state/{sid}.json'
        rec.update(raw_measurement_file=rf,raw_file_sha256=sha(P/rf),method_source='source_genesis_next_v2/genesis_next/assay.py (assay_state), genesis_next/solvers.py, genesis_next/numerics.py',
          numeric_qualification='results/NUMERICAL_QUALIFICATION.csv (QUALIFIED; thresholds in results/FOLLOWUP_LOCK.json config)',
          delta=float(x['delta']),F_star=float(x['F_star']),block_val_gain=float(x['block_val_gain']),full_val_gain=float(x['full_val_gain']),
          cg_grid_k_matching_block_gain=x['cg_grid_k_matching_block_gain'],cg_matching_wall_ratio_vs_block=x['cg_matching_wall_ratio_vs_block'],
          null_energy_fraction=float(x['null_energy_fraction']),gradient_null_fraction=float(x['gradient_null_fraction']),inverse_offdiag_fraction=float(x['inverse_offdiag_fraction']),
          gradient_weighted_n99=x['gradient_weighted_n99'],effective_gain_directions=float(x['effective_gain_directions']),
          limits='S1 exploratory; DLN only; CPU FP64; condition is NOT an independent seed (unit = training seed)')
    else:
        rec.update(raw_measurement_file=None,limits='no measurement: '+str(row['reason']))
    ev.append(rec)
(P/'EVIDENCE_INDEX.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in ev))
# claims computed directly from raw per-state JSONs
conds=[(r,c) for r in res.values() for c in r['conditions']]
n=len(conds)
valid=sum(c['status']=='QUALIFIED' for r,c in conds)
def cgmatch(c):
    tgt=1-c['delta'];return any(x['name'].startswith('cg_') and x['gain_ratio']>=tgt for x in c['comparators'])
negB=sum(c['block_ray_loss']['validation_gain']<0 for r,c in conds);negF=sum(c['full_loss']['validation_gain']<0 for r,c in conds)
seeds={(r['setting_id'],r['seed']) for r in res.values()}
e4=[c['e4_delta_attribution'] for r,c in conds]
v2err=[abs(a['v2_total_error']) for a in e4 if 'v2_total_error' in a]
ids=lambda f:[f'{r["state_id"]}:{c["gamma"]}' for r,c in conds if f(r,c)]
cl=[
 ('C1','All 114 measured conditions pass the numerical qualification (dense autograd reference, alternate operator, gradient crosscheck, full-direction error, dense-vs-CG delta, bounds).',{'conditions':n,'qualified':valid},'results/per_state/*.json (conditions[].status, reason); results/NUMERICAL_QUALIFICATION.csv','genesis_next/assay.py lines for QUALIFIED gate; thresholds in FOLLOWUP_LOCK.json config','recompute_from_raw.py C1','Qualification is a numerical-reference criterion, not a scientific success label.'),
 ('C2','CG reaches Block gain (quadratic) within the 1..64 grid in every condition; CG solve wall at matching budget is a small fraction of Block wall.',{'cg_matches_block':sum(cgmatch(c) for r,c in conds),'of':n},'results/per_state/*.json comparators; results/CG_COST_COMPARISON.csv','genesis_next/assay.py (comparator loop), solvers.py cg','recompute_from_raw.py C2','Wall clock is single-run diagnostic timing on a shared CPU, fixed order; matvec-matched CG is a separate enforced budget. Grid-censored first crossing.'),
 ('C3','Inverse-curvature energy is concentrated in the GGN near-null space while the gradient projection onto it is ~0; gradient-conditioned dimension is small.',{'max_gradient_null_fraction':max(c['geometry'][1]['gradient_null_fraction'] for r,c in conds),'min_null_energy_fraction':min(c['geometry'][1]['null_energy_fraction'] for r,c in conds)},'results/per_state/*.json geometry[1]; results/STRUCTURE_MECHANISM_RESULTS.jsonl','genesis_next/numerics.py dense_geometry (rank_rtol 1e-8 = geometry index 1)','recompute_from_raw.py C3','Null-energy fraction is partly mechanical (nullity/gamma). Threshold-defined near-null; 3 tolerances stored.'),
 ('C4','FP32 vs FP64 delta: v2 recorded delta vs FP64 reference, input-quantization and FP32-arithmetic effects separated.',{'v2_valid_rows':len(v2err),'v2_abs_err_gt_1e-3':sum(x>1e-3 for x in v2err),'v2_unresolved_but_fp64_valid':sum(a['v2_recorded_status']!='NUMERIC_VALID' for a in e4)},'results/NUMERICAL_ERROR_AUDIT.jsonl; per-state conditions[].e4_delta_attribution','genesis_next/assay.py (dense_delta, e4 block)','recompute_from_raw.py C4','Attribution is for dense DLN only; solver error of v2 is the residual, not isolated.'),
 ('C5','Validation (single step, train-selected step size) gain is negative in most conditions for both Block and full solve.',{'block_negative':negB,'full_negative':negF,'denominator_conditions':n,'denominator_states':len(res),'independent_seeds':len(seeds)},'results/per_state/*.json conditions[].block_ray_loss/full_loss','genesis_next/assay.py loss_trials','recompute_from_raw.py C5','Single frozen batch; gains ~1e-7; denominators are conditions on 19 seeds, not 114 seeds.'),
 ('C6','H1 supported within tested scope (DLN only).',{'basis':'C3 plus negative within-gamma Spearman(inverse_offdiag, delta) in results/STRUCTURE_UTILITY_ASSOCIATIONS.csv'},'results/STRUCTURE_UTILITY_ASSOCIATIONS.csv; C3','analysis/make_deliverables.py','see C3 and associations CSV','Descriptive; conditions share seeds; pooled association flips sign.'),
 ('C7','H2 contradicted within tested scope (DLN only); nonlinear NOT_YET_TESTED.',{'basis':'C2'},'C2 evidence','analysis/make_deliverables.py','see C2','No nonlinear data; S1 exploratory, not confirmation.'),
 ('C8','Coverage: 38 of 80 states executed (114 of 240 conditions); 42 states / 126 conditions SOURCE_NOT_READY.',{'executed_states':len(res),'planned_states':80,'executed_conditions':n,'planned_conditions':240},'derived/state_denominator_80.csv; results/EXPERIMENT_INVENTORY.csv','genesis_next/ledger.py','recompute_from_raw.py C8','Missing states are retained in the denominator; no replacement.')]
with (P/'CLAIM_LEDGER.jsonl').open('w') as f:
    for cid,txt,val,ef,ms,rc,lim in cl:
        efs=[e.split(' ')[0].strip(';') for e in ef.split(';')]
        f.write(json.dumps({'claim_id':cid,'claim':txt,'computed_value_at_packaging':val,'evidence_files':ef,'method_source':ms,'recompute_with':rc,'numerical_qualification':'see C1','limitation':lim,
          'independence_unit':'training seed (19 seeds across 4 DLN settings); conditions are correlated measurements',
          'condition_ids_state_gamma':ids(lambda r,c:True) if cid in ('C1','C2','C3','C4','C5') else None})+'\n')
# validation-gain denominator evidence
with (P/'derived/validation_gain_per_condition.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['state_id','setting_id','seed','checkpoint','gamma','train_loss','block_train_gain','block_val_gain','full_train_gain','full_val_gain'])
    for r,c in conds:w.writerow([r['state_id'],r['setting_id'],r['seed'],r['checkpoint'],c['gamma'],c['block_ray_loss']['train_loss'],c['block_ray_loss']['train_gain'],c['block_ray_loss']['validation_gain'],c['full_loss']['train_gain'],c['full_loss']['validation_gain']])
print(n,valid,negB,negF,len(seeds),len(res),'tests rc',t.returncode)
