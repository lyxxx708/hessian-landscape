"""Per-(state,gamma) condition ledger. Committed results are never rewritten."""
from __future__ import annotations

def condition_ledger(lock,results,source_ready,running=()):
    rows=[]
    for st in lock['plan']['states']:
        sid=st['state_id'];r=results.get(sid);run=st['run']
        by={float(c['gamma']):c for c in (r or {}).get('conditions',[])}
        for g in lock['config']['gammas']:
            c=by.get(float(g))
            if c is not None:
                status='NUMERIC_VALID' if c['status']=='QUALIFIED' else 'NUMERIC_UNRESOLVED'
            elif r is not None and r.get('status')=='TIMEOUT_INCONCLUSIVE':status='TIMEOUT_INCONCLUSIVE'
            elif r is not None and r.get('status')=='EXECUTION_ERROR':status='FAILED'
            elif r is not None and r.get('status')=='EXECUTED':status='READY'
            elif sid in running:status='RUNNING'
            elif not source_ready.get(sid,False):status='SOURCE_NOT_READY'
            else:status='READY'
            rows.append({'state_id':sid,'family':run['model']['family'],'setting_id':run['setting_id'],
                         'seed_index':run['seed_index'],'checkpoint':st['checkpoint_index'],'gamma':g,'status':status,
                         'reason':(c or {}).get('reason') or (r or {}).get('reason')})
    return rows
