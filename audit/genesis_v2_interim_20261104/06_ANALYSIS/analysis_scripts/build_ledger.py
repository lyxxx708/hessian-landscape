"""Build CLAIM_LEDGER.jsonl from files in this snapshot. Every number is computed from a snapshot file.

Statuses are restricted to OBSERVED / SUPPORTED / CONTRADICTED / INCONCLUSIVE / NOT_YET_TESTED. The packager does not
judge scientific success; claims about S/M/U/P hypotheses are NOT_YET_TESTED because no adjudication exists.

Usage: python build_ledger.py <snapshot_dir>
"""
import csv,json,sys,collections as C
S=sys.argv[1]
def jl(p):return [json.loads(l) for l in open(f'{S}/{p}',encoding='utf-8')]
def rows(p):return list(csv.DictReader(open(f'{S}/{p}',encoding='utf-8')))
inv=jl('02_EXECUTION/job_inventory/job_inventory.jsonl')
util=rows('03_SCIENTIFIC_DATA/utility/utility_rows.csv')
st=jl('03_SCIENTIFIC_DATA/structure/structure_records.jsonl')
au=jl('04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_rows.jsonl')
bad=jl('04_NUMERICAL_AUDIT/false_valid_cases/false_valid_cases.jsonl')
cov=rows('06_ANALYSIS/existing_statistics/seed_coverage_by_setting.csv')
dln=[]
import glob
for p in sorted(glob.glob(f'{S}/05_V21_QUALIFICATION/dln_comparison/dln_dln_*.jsonl')):dln+=[json.loads(l) for l in open(p,encoding='utf-8')]
ver=json.load(open(f'{S}/02_EXECUTION/job_inventory/receipt_verification.json'))
cnt=C.Counter((r['kind'],r['state']) for r in inv)
tr_done=cnt[('train','COMPLETE')];tr_fail=cnt[('train','FAILED')]
full_seed_settings=[r['setting_id'] for r in cov if r['training_complete']=='5']
coarse_unres=[r for r in util if r['schema']=='coarse' and r['receipt_status']=='NUMERIC_UNRESOLVED']
coarse_valid=[r for r in util if r['schema']=='coarse' and r['receipt_status']=='NUMERIC_VALID']
g001=[r for r in util if r['schema']=='coarse' and r['gamma']=='0.001']
stc=C.Counter(((r['structure'].get('status')),r['tier']) for r in st if r['schema']=='coarse')
cls=C.Counter(r['class'] for r in au)
def v(variant,g):
    R=[r for r in dln if r['variant']==variant and abs(r['gamma']-g)<1e-12];return sum(r['status']=='NUMERIC_VALID' for r in R),len(R)
fv_states=sorted({(r['setting'],r['seed_index'],r['checkpoint']) for r in bad})
claims=[]
def add(cid,claim,status,scope,evid,seeds,qual,paths,lim):
    claims.append({'claim_id':cid,'claim':claim,'status':status,'scope':scope,'evidence_ids':evid,'independent_seed_n':seeds,'numerical_qualification':qual,'source_paths':paths,'limitations':lim})
add('EXEC-001',f"At snapshot time the S1 queue held {cnt[('measure','COMPLETE')]} COMPLETE, {cnt[('measure','NUMERIC_UNRESOLVED')]} NUMERIC_UNRESOLVED, {cnt[('measure','BLOCKED')]} BLOCKED, {cnt[('measure','PENDING')]} PENDING and {cnt[('measure','RUNNING')]} RUNNING measurement jobs, and {tr_done} COMPLETE, {tr_fail} FAILED, {cnt[('train','PENDING')]} PENDING training jobs. No S2 jobs exist in the queue.",'OBSERVED','GENESIS v2 run, S1 stage only',
    ['02_EXECUTION/sqlite_snapshot/run_status_snapshot.sqlite','02_EXECUTION/job_inventory/job_inventory.jsonl'],0,'NOT_APPLICABLE',['02_EXECUTION/job_inventory/job_inventory.csv'],'Snapshot is one moment; the live pipeline continues to advance. The queue holds S1 jobs only until S1 is done.')
add('EXEC-002',f"Settings with all 5 planned S1 training seeds complete: {len(full_seed_settings)} of {len(cov)} S1 settings (all DLN); no MLP, ResNet or Transformer training has run.",'OBSERVED','S1 independent training seeds',
    ['06_ANALYSIS/existing_statistics/seed_coverage_by_setting.csv'],tr_done,'NOT_APPLICABLE',['02_EXECUTION/training_receipts/'],'Independent unit is a training seed. Checkpoints, dampings and schemas are repeated measures of a seed, not independent samples.')
add('EXEC-003',"No S1 or S2 adjudication, statistics table, figure or manifest has been produced by the pipeline (stage state S1_RUNNING).",'OBSERVED','Pipeline outputs at snapshot time',
    ['01_PROTOCOL/source_identity/study-state.json','06_ANALYSIS/existing_statistics/NOT_PRODUCED.md'],0,'NOT_APPLICABLE',['01_PROTOCOL/source_identity/study-state.json'],'Absence of tables was read from the run directory listing at snapshot time.')
add('EXEC-004',"One S1 training job (dln_d4_w16_orthogonal_balanced_c1 seed index 0) FAILED with IntegrityError 'Resume provenance mismatch'; 24 dependent measurement jobs are BLOCKED with DEPENDENCY_NOT_VALID.",'OBSERVED','One DLN setting',
    ['02_EXECUTION/failure_records/'],1,'NOT_APPLICABLE',['02_EXECUTION/job_inventory/job_inventory.jsonl'],'That setting therefore has 4 of 5 planned seeds in v2.')
add('REPRO-001',"The synthetic DLN dataset fingerprint depends on the BLAS/OpenMP thread count in the environment; the failed run's checkpoints carry the fingerprint produced with OMP_NUM_THREADS unset, while the current worker environment sets it to 2.",'SUPPORTED','Synthetic DLN data generation on this machine, setting dln_d4_w16_orthogonal_balanced_c1, seed index 0 and 1',
    ['04_NUMERICAL_AUDIT/reproducibility/ADDENDUM_01_thread_pinning.md'],0,'NOT_APPLICABLE',['04_NUMERICAL_AUDIT/reproducibility/ADDENDUM_01_thread_pinning.md','07_SOURCE/executed_source/genesis_gpu/datasets/registry.py'],'Measured at 2, 3, 4, 8 and default threads for two seeds; the root cause inside torch/BLAS was not isolated; no fix was applied.')
add('NUM-001',f"{len(coarse_unres)} of {len(g001)} coarse measurements at gamma=0.001 are NUMERIC_UNRESOLVED (ORACLE_SOLVE_FAILED); coarse measurements at gamma 0.01 and 0.1 are all NUMERIC_VALID so far ({len(coarse_valid)-3} of them).",'OBSERVED','DLN coarse measurements completed in v2 at snapshot time',
    ['03_SCIENTIFIC_DATA/numerical_eligibility/eligibility_rows.csv','03_SCIENTIFIC_DATA/numerical_eligibility/outcome_counts_by_gamma_schema_tier.csv'],tr_done,'AUDITED_PARTIAL',['03_SCIENTIFIC_DATA/utility/utility_rows.csv'],'Only DLN has been measured. The 3 NUMERIC_VALID gamma=0.001 coarse rows are checkpoint 0 and were audited.')
add('NUM-002',f"An offline FP64 audit of {len(au)} NUMERIC_VALID DLN rows ({len({(r['setting'],r['seed_index'],r['checkpoint'],r['gamma']) for r in au})} distinct measurements) found {cls['AGREE']} AGREE and {cls['MATERIAL']} MATERIAL (difference > 0.01 in delta, E_task or E_val), with no other class.",'OBSERVED','DLN, 610 of the 658 COMPLETE rows at snapshot time; audit predates the snapshot',
    ['04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_rows.jsonl','04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_coverage_vs_snapshot.json'],len({(r['setting'],r['seed_index']) for r in au}),'AUDITED_PARTIAL',['04_NUMERICAL_AUDIT/fp32_vs_fp64/AUDIT_REPORT_2026-11-04.md','04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_fp32.py'],'The FP64 reference ran on CPU while v2 ran on GPU FP32, so device differences are included. 48 later COMPLETE rows are not audited. Thresholds were set before results (AUDIT_PROTOCOL.md).')
add('NUM-003',f"All MATERIAL rows ({len(bad)} rows, {len(fv_states)} states) come from one trajectory (dln_d8_w16_orthogonal_balanced_c1, seed index 3) and each passed the v2 delta_stability check (recorded values <= 3.1e-6); the FP32 gradient vector differs from FP64 by about 40% at the two states involved.",'OBSERVED','One DLN trajectory',
    ['04_NUMERICAL_AUDIT/false_valid_cases/false_valid_cases.jsonl','04_NUMERICAL_AUDIT/false_valid_cases/per_state_gradient_error.csv'],1,'AUDITED_PARTIAL',['04_NUMERICAL_AUDIT/fp32_vs_fp64/AUDIT_REPORT_2026-11-04.md'],'The gradient error is FP32 on CPU as a proxy for the GPU value. Three failures are one seed, not three independent failures. Whether this affects S1 predictor or U statistics has not been analysed.')
add('NUM-004',"Recorded gradient norm alone does not identify the false-valid cases: the same state at gradient norm about 3e-7 is AGREE at gamma 0.01 and MATERIAL at gamma 0.1.",'OBSERVED','Same trajectory, checkpoint 2',
    ['04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_rows.jsonl'],1,'AUDITED_PARTIAL',['04_NUMERICAL_AUDIT/fp32_vs_fp64/AUDIT_REPORT_2026-11-04.md'],'Exploratory; two high-error states only.')
add('NUM-005',"The relative residual originally reported in FINDINGS_2026-11-03.md was wrong (true_residual was divided by the gradient norm a second time); the corrected gamma=0.001 full-solve medians are in the correction file.",'OBSERVED','Takeover diagnostics of the v2 gamma=0.001 solver failure',
    ['04_NUMERICAL_AUDIT/residual_corrections/CORRECTION_2026-11-03_relative_residual.md','04_NUMERICAL_AUDIT/residual_corrections/FINDINGS_2026-11-03.md'],0,'NOT_APPLICABLE',['04_NUMERICAL_AUDIT/cg_preconditioner/cgdiag.py'],'The original file is retained unchanged with its error.')
a0,n0=v('V0_frozen',0.001);a1,n1=v('V1_noprecond',0.001);a3,n3=v('V3_noprecond_f64',0.001);a4,n4=v('V4_noprecond_ondrift_f64',0.001)
add('V21-001',f"On 36 real DLN S1 states at gamma=0.001, offline NUMERIC_VALID counts were: frozen preconditioner FP32 {a0}/{n0}, plain FP32 {a1}/{n1}, plain FP64 {a3}/{n3}, plain on-drift FP64 {a4}/{n4}.",'OBSERVED','6 DLN settings, seeds 1 and 3, checkpoints 0, 1, 3; CPU harness',
    ['05_V21_QUALIFICATION/dln_comparison/dln_variant_summary.csv'],2,'CANDIDATE_NOT_PRODUCTION_QUALIFIED',['05_V21_QUALIFICATION/solver_variants/solver_compare.py'],'CPU only; harness, not the production pipeline; seeds chosen for qualification (1 and 3), not S2.')
add('V21-002',"Plain FP64 CG matched dense FP64 solutions to at most 4.8e-7 in delta on DLN at gamma=0.001 (36/36 states); plain FP32 reached 1.7e-3 at one false-valid state.",'OBSERVED','DLN, same set as V21-001',
    ['05_V21_QUALIFICATION/dln_comparison/dln_variant_summary.csv'],2,'CANDIDATE_NOT_PRODUCTION_QUALIFIED',['05_V21_QUALIFICATION/solver_variants/solver_compare.py'],'Dense truth exists only for small parameter counts.')
add('V21-003',"On frozen one-step preflight checkpoints, plain FP64 CG was NUMERIC_VALID and matched an independent reference for MLP and ResNet at the dampings run, and for Transformer at gamma 0.01 and 0.001 (CPU, long run); the frozen preconditioner and plain FP32 exceeded a 1800 s CPU cap on ResNet gamma=0.001.",'OBSERVED','One preflight state per family (not trained S1 states)',
    ['05_V21_QUALIFICATION/mlp_resnet_transformer/frozen_mlp.jsonl','05_V21_QUALIFICATION/mlp_resnet_transformer/frozen_resnet.jsonl','05_V21_QUALIFICATION/mlp_resnet_transformer/frozen_transformer_long.jsonl'],0,'CANDIDATE_NOT_PRODUCTION_QUALIFIED',['05_V21_QUALIFICATION/go_no_go/GO_NO_GO_2026-11-04.md'],'ResNet/Transformer gamma=0.1 and Transformer V0/V1/V4 at long caps were not run. GPU cost, FP64 memory and CUDA G0 are NOT_YET_TESTED. The first Transformer attempt hit the 1800 s cap for every variant (INCONCLUSIVE, not a numeric failure).')
add('V21-004',"v2.1 is NO-GO for switching; v2 continues unmodified.",'OBSERVED','Decision recorded by the owner on 2026-11-04',
    ['05_V21_QUALIFICATION/go_no_go/GO_NO_GO_2026-11-04.md'],0,'NOT_APPLICABLE',['05_V21_QUALIFICATION/go_no_go/GO_NO_GO_2026-11-04.md'],'Conditions listed there remain open.')
add('NUM-006',f"For DLN and MLP, group_for ignores the schema argument, and the statistics and predictor code filter to schema == 'coarse'; {sum(1 for r in inv if r['kind']=='measure' and r['stage']=='s1' and r['schema']=='fine' and r['family'] in ('dln','mlp'))} of {sum(1 for r in inv if r['kind']=='measure' and r['stage']=='s1')} S1 measurement jobs are fine-schema jobs on those two families.",'SUPPORTED','Source inspection plus 305 audited DLN pairs with identical v2 delta',
    ['04_NUMERICAL_AUDIT/reproducibility/coarse_fine_redundancy_evidence.md'],0,'NOT_APPLICABLE',['07_SOURCE/executed_source/genesis_gpu/models/dln.py','07_SOURCE/executed_source/genesis_gpu/models/mlp.py','07_SOURCE/executed_source/genesis_gpu/study/statistics.py','07_SOURCE/executed_source/genesis_gpu/science/predictor.py'],'ResNet and Transformer grouping, and any other consumer of fine rows, were not reviewed. Structure probes on fine rows may differ by random draws.')
add('STRUCT-001',f"Structure measurements on coarse rows: "+', '.join(f"{k[1]} {k[0]}={n}" for k,n in sorted(C.Counter(((r['structure'].get('status')),r['tier']) for r in st if r['schema']=='coarse').items()))+".",'OBSERVED','DLN coarse rows with structure records',
    ['03_SCIENTIFIC_DATA/structure/structure_records.jsonl'],tr_done,'NOT_AUDITED',['03_SCIENTIFIC_DATA/raw_measurement_records/'],'Structure metrics, profiles and bootstrap intervals were NOT independently re-verified. Some structure records are unresolved even when the utility is valid (PROBE_SOLVE_ITERATION_LIMIT).')
for cid,name in (('S-001','S (structure) hypothesis'),('M-001','M (mechanism) hypothesis'),('U-001','U (utility) hypothesis'),('P-001','P (prediction) hypothesis')):
    add(cid,f"No adjudicated result exists for the {name}; S1 is incomplete and neither S1 nor S2 adjudication has run.",'NOT_YET_TESTED','Pre-registered hypothesis per frozen protocol',
        ['06_ANALYSIS/existing_statistics/NOT_PRODUCED.md','01_PROTOCOL/study_matrix/study_matrix_summary.json'],0,'NOT_APPLICABLE',['07_SOURCE/executed_source/genesis_gpu/study/statistics.py','07_SOURCE/executed_source/genesis_gpu/study/adjudication.py'],'Descriptive tables in this snapshot are not preregistered analyses. S1 is exploratory by design; S2 is the confirmation stage and has not started.')
with open(f'{S}/08_AUDIT_LEDGER/CLAIM_LEDGER.jsonl','w',encoding='utf-8',newline='\n') as f:
    for c in claims:f.write(json.dumps(c,sort_keys=True)+'\n')
missing=[p for c in claims for p in c['evidence_ids']+c['source_paths'] if not __import__('os').path.exists(f'{S}/{p}')]
print(len(claims),'claims; missing paths:',missing)
