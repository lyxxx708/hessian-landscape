"""Summarize audit_rows.jsonl. Descriptive; classes come from audit_fp32.py."""
import json,collections as C,statistics as st,sqlite3
rows=[json.loads(l) for l in open('E:/GENESIS/evidence/v2_numeric_audit/audit_rows.jsonl',encoding='utf-8')]
print('rows',len(rows),'states',len({(r['setting'],r['seed_index'],r['checkpoint']) for r in rows}),'settings',len({r['setting'] for r in rows}))
print('class',C.Counter(r['class'] for r in rows))
print('by gamma',sorted(C.Counter((r['gamma'],r['schema'],r['class']) for r in rows).items()))
D=lambda r,k:abs(r[f'v2_{k}']-r[f'ref_{k}'])
for k in ('delta','E_task','E_val','cheap_rho','F_star'):
    x=[D(r,k) for r in rows if r[f'v2_{k}'] is not None and r[f'ref_{k}'] is not None]
    x.sort();print(k,len(x),'med %.2e p99 %.2e max %.2e'%(st.median(x),x[int(.99*len(x))],x[-1]))
g=sorted({(r['setting'],r['seed_index'],r['checkpoint']):r['grad_rel_err'] for r in rows}.values());print('grad_rel_err med %.2e p99 %.2e max %.2e'%(st.median(g),g[int(.99*len(g))],g[-1]))
x=[abs(r['ref_delta']-r['dense_delta']) for r in rows if r['dense_delta'] is not None and r['ref_delta'] is not None];print('ref vs dense',len(x),'max %.2e'%max(x))
print('--- nonAGREE')
for r in sorted(rows,key=lambda r:-max(D(r,k) for k in ('delta','E_task','E_val')) if r['ref_delta'] is not None else 0):
    if r['class']!='AGREE':
        print(r['class'],r['setting'],'s',r['seed_index'],'c',r['checkpoint'],r['gamma'],r['schema'],'|g| %.2e gerr %.2e cos-1 %.1e'%(r['grad_norm_fp64'],r['grad_rel_err'],r['grad_cos']-1),'d',r['v2_delta'],r['ref_delta'],'Et',r['v2_E_task'],r['ref_E_task'],'Ev',r['v2_E_val'],r['ref_E_val'],'stab',r['v2_delta_stability'],r['v2_task_status'],r['ref_task_status'],r['ref_reason'])
print('--- largest AGREE D')
ag=sorted([r for r in rows if r['class']=='AGREE'],key=lambda r:-max(D(r,k) for k in ('delta','E_task','E_val')))[:8]
for r in ag:print(r['setting'],r['seed_index'],r['checkpoint'],r['gamma'],r['schema'],'D %.2e |g| %.2e gerr %.2e'%(max(D(r,k) for k in ('delta','E_task','E_val')),r['grad_norm_fp64'],r['grad_rel_err']))
print('--- predictors: state gerr vs max D')
s=C.defaultdict(list)
for r in rows:s[(r['setting'],r['seed_index'],r['checkpoint'])].append(r)
t=sorted(((v[0]['grad_rel_err'],v[0]['grad_norm_fp64'],max(D(r,'delta') for r in v),k) for k,v in s.items()),reverse=True)[:12]
for a in t:print('gerr %.2e |g| %.2e maxDdelta %.2e'%a[:3],a[3])
db=sqlite3.connect('file:E:/GENESIS/runs/genesis_full_v2/run_status.sqlite?mode=ro',uri=True)
print(db.execute("select state,count(*) from jobs group by 1").fetchall())
