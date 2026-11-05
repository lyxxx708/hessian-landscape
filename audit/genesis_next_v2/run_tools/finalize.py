import json,csv,hashlib,glob,subprocess,time
from pathlib import Path
O=Path(r'E:\GENESIS\runs\genesis_next_v2')
res=[json.loads(p.read_text(encoding='utf-8')) for p in (O/'results').glob('*.json')]
wall=[r.get('wall_seconds',0) for r in res]
cov=json.loads((O/'COVERAGE.json').read_text())
lock=json.loads((O/'FOLLOWUP_LOCK.json').read_text())
v2=Path(r'E:\GENESIS\runs\genesis_full_v2')
hb=json.loads((v2/'heartbeat.json').read_text())
state={'study':'GENESIS NEXT v2','freeze_sha':lock['freeze_sha'],'updated_epoch':time.time(),'state':'PARTIAL_COMPLETE_DLN_PANEL_DONE_NONLINEAR_SOURCE_NOT_READY',
 'coverage':cov,'driver':'exited normally (no pending ready work)','state_results':len(res),
 'sum_state_wall_seconds':sum(wall),'max_state_wall_seconds':max(wall),
 'v2_worker_at_finalize':{'heartbeat_counts':hb['counts'],'heartbeat_epoch':hb['time'],'now_epoch':time.time()},
 'resume':'python -m genesis_next drive --out E:\\GENESIS\\runs\\genesis_next_v2 --device cpu --workers 4 --approve-compute (with OMP_NUM_THREADS=2, PYTHONPATH=worktree); it commits only newly source-ready states'}
(O/'NEXT_V2_EXECUTION_STATE.json').write_text(json.dumps(state,indent=2))
print(state['sum_state_wall_seconds'],state['max_state_wall_seconds'],hb['counts'],time.time()-hb['time'])
