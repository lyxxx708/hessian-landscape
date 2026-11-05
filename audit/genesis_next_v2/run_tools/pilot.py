import sys,json,time
sys.path.insert(0,r'E:\GENESIS\worktrees\genesis-next-v2')
from pathlib import Path
from genesis_next.planning import freeze,validate_freeze
from genesis_next.assay import assay_state
from genesis_next.io_utils import read_json
pkg=Path(r'E:\GENESIS\worktrees\genesis-next-v2')
bundle=Path(r'E:\GENESIS\handoff\audit_snapshot_20261104_201035')
out=Path(r'E:\GENESIS\runs\genesis_next_v2\_dev_pilot2')
f=freeze(bundle,bundle/'07_SOURCE/executed_source',Path(r'E:\GENESIS\runs\genesis_full_v2'),out,pkg/'configs/protocol_v2.json',pkg,'cpu')
print(f['freeze_sha'])
sid='41c00898702c'
st=[s for s in f['plan']['states'] if s['state_id'].startswith(sid)][0]
t=time.time()
r=assay_state(f,st,'cpu',out)
print(time.time()-t,r['status'],[ (c['gamma'],c['status'],c.get('reason')) for c in r['conditions']])
json.dump(r,open(out/'pilot_result.json','w'),indent=1,default=str)
