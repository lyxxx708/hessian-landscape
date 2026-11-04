"""Export job inventory and verified receipt shards from the SQLite snapshot (read-only on the live run).

Usage: python export_inventory.py <snapshot_dir> <run_root>
"""
import csv,hashlib,json,os,sqlite3,sys,collections as C
snap,root=sys.argv[1],sys.argv[2]
db=sqlite3.connect(f'file:{snap}/02_EXECUTION/sqlite_snapshot/run_status_snapshot.sqlite?mode=ro',uri=True)
cols=[c[1] for c in db.execute('pragma table_info(jobs)')]
jobs=[dict(zip(cols,r)) for r in db.execute('select * from jobs order by ordinal')]
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
inv=[];verify=[]
for j in jobs:
    p=json.loads(j['payload']);r=json.loads(j['result']) if j['result'] else {}
    run=p.get('run',{});rc=r.get('receipt') or {}
    row={'job_id':j['id'],'ordinal':j['ordinal'],'stage':j['stage'],'kind':j['kind'],'state':j['state'],'attempts':j['attempts'],
         'family':run.get('model',{}).get('family'),'setting_id':run.get('setting_id'),'run_id':run.get('run_id'),'seed_index':run.get('seed_index'),'seed':run.get('seed'),
         'checkpoint_index':p.get('checkpoint_index'),'gamma':p.get('gamma'),'schema':p.get('schema'),'tier':p.get('tier'),
         'measurement_status':r.get('measurement_status'),'error':r.get('error'),'reason':r.get('reason'),'dependencies':j['dependencies'],
         'receipt_path':rc.get('path'),'receipt_bytes':rc.get('bytes'),'receipt_sha256':rc.get('sha256'),'updated_epoch':j['updated'],'heartbeat_epoch':j['heartbeat'],'pid':j['pid']}
    if rc.get('path'):
        f=os.path.join(root,rc['path']);st='MISSING'
        if os.path.exists(f):
            st='OK' if (os.path.getsize(f)==rc['bytes'] and sha(f)==rc['sha256']) else 'MISMATCH'
        row['receipt_verify']=st;verify.append((j['id'],st))
    inv.append(row)
out=f'{snap}/02_EXECUTION/job_inventory'
keys=list(dict.fromkeys(k for r in inv for k in r))
with open(f'{out}/job_inventory.jsonl','w',encoding='utf-8',newline='\n') as f:
    for r in inv:f.write(json.dumps(r,sort_keys=True)+'\n')
with open(f'{out}/job_inventory.csv','w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,keys);w.writeheader();w.writerows(inv)
print('jobs',len(inv),C.Counter(v for _,v in verify),C.Counter((r['kind'],r['state']) for r in inv))
json.dump({'verified':dict(C.Counter(v for _,v in verify)),'non_ok':[(a,b) for a,b in verify if b!='OK']},open(f'{out}/receipt_verification.json','w'),indent=1)
