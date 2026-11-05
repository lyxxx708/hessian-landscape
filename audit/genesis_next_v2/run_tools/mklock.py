import json,hashlib
from pathlib import Path
O=Path(r'E:\GENESIS\runs\genesis_next_v2')
lock=json.loads((O/'FOLLOWUP_LOCK.json').read_text(encoding='utf-8'))
h=hashlib.sha256((O/'FOLLOWUP_LOCK.json').read_bytes()).hexdigest()
wrapper={
 'schema':1,'study':'GENESIS NEXT v2','created_beijing':'2026-11-06T00:15+08:00; freeze #2 after infra fix: child-ownership check used parent PID, failed behind the venv launcher shim; first freeze 178898216f22 archived in _superseded_freeze1, no science measured (before any frozen-panel measurement)',
 'machine_lock':'FOLLOWUP_LOCK.json','machine_lock_file_sha256':h,'freeze_sha':lock['freeze_sha'],
 'evidence_class':'POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION',
 'audit_commit_inherited':'629032110fa51affc7f4e96cdb75f0c40070a9fe',
 'inherited_from':'GENESIS NEXT v1 (read-only copy; source copied to E:/GENESIS/worktrees/genesis-next-v2)',
 'sample_frame':{'settings':8,'seeds_per_setting':5,'checkpoints':[1,3],'gammas':[0.001,0.01,0.1],'states':80,'conditions':240,'order':'frozen plan order; Q0 (seed 1, ckpt 3) first; selection never depends on observed delta'},
 'p0_findings_before_measurement':{
   'v2_worker':'PID 73000 alive, queue advancing (heartbeat age ~1 min), GPU use ~1.5 GiB of 12 GiB, util 10-40%',
   'gpu_preemption':'NOT performed. 42 of 80 planned states have no COMPLETE S1 training receipt (MLP/ResNet/Transformer untrained; v2 queue reaches them only after ~1000 pending DLN jobs). A GPU window would produce no new evidence, and FP64 on this consumer GPU is not faster than CPU for these dense DLN assays. All frozen-panel work therefore runs on CPU, read-only against v2 receipts.',
   'v2_modified':False},
 'fixes_vs_v1_each_with_regression_test':[
   'safety.require_exclusive: CPU assays no longer blocked by live v2 worker (CUDA gate unchanged) [tests/test_v2.py]',
   'cli.qualified_conditions: Q0 gating is per (family,gamma) instead of all-three-gammas [tests/test_v2.py]',
   'ledger.condition_ledger: per (state,gamma) status PLANNED/READY/RUNNING/NUMERIC_VALID/NUMERIC_UNRESOLVED/TIMEOUT_INCONCLUSIVE/FAILED/SOURCE_NOT_READY [tests/test_v2.py]',
   'cli.drive: unattended OS-process driver, parallel children, 1800 s per-state timeout, heartbeat, STOP file, results never overwritten',
   'cli.is_ancestor: child ownership check accepts any ancestor (venv shim) [tests/test_v2.py]','cli.drive: launch failures within 20 s are logged to infra_failures/ and never committed as results','assay.e4_delta_attribution: delta from native-FP64 inputs and from FP32 arithmetic on the same rounded inputs, to separate input quantization from arithmetic error'],
 'execution':{'device':'cpu','dtype':'float64','threads_per_child':2,'workers':4,'per_state_timeout_s':1800,'deadline_stop_new_work':'2026-11-06T07:00+08:00'},
 'analysis_plan_fixed_before_data':{
   'independent_unit':'training seed (median over checkpoints 1,3 within seed, then across seeds)',
   'H1_evidence':'null_energy_fraction vs gradient_null_fraction, active vs null off-diagonal fractions, delta vs inverse_offdiag_fraction rank association across settings/gammas (descriptive, Spearman, seed-cluster bootstrap 2000 reps seed 20261105)',
   'H2_evidence':'matched_matvec_cg and fixed-k CG gain ratios vs Block; wall-clock ratio solve_wall_vs_block; Block counts as winning only if gain_ratio_of_CG < 1 at budget AND wall of CG >= wall of Block',
   'labels':['SUPPORTED_WITHIN_TESTED_SCOPE','CONTRADICTED_WITHIN_TESTED_SCOPE','INCONCLUSIVE','NOT_YET_TESTED'],
   'nonlinear_families':'NOT_EVALUABLE unless COMPLETE S1 training receipts appear; no G0/initial-state substitution; no self-trained substitute counted in the frozen panel'}}
(O/'NEXT_V2_PROTOCOL_LOCK.json').write_text(json.dumps(wrapper,indent=2,ensure_ascii=False),encoding='utf-8')
print(h)
