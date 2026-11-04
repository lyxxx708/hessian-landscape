"""Summarize solver-qualification JSONL by variant and damping (read-only)."""
import collections,glob,json,math,sys
import numpy as np
rows=[json.loads(l) for f in glob.glob(sys.argv[1]) for l in open(f,encoding='utf-8')]
print('rows',len(rows))
by=collections.defaultdict(list)
for r in rows:by[(r.get('family','dln') if 'family' in r else 'dln',r['gamma'],r['variant'])].append(r)
med=lambda v:float(np.median(v)) if v else float('nan')
for k in sorted(by):
    v=by[k];ok=[r for r in v if r['status']=='NUMERIC_VALID']
    reasons=collections.Counter(r.get('reason') for r in v if r['status']!='NUMERIC_VALID')
    dd=[abs(r['delta']-r['dense_delta']) for r in ok if r.get('dense_delta') is not None and r.get('delta') is not None]
    ps=[p for r in v for p in r.get('probe_solves',[])]
    print(k,f"n={len(v)} valid={len(ok)} full_it={med([r['full_it'] for r in v if r.get('full_it')]):.0f} tight_it={med([r['tight_it'] for r in v if r.get('tight_it')]):.0f}"
          f" budget={med([r['matched_budget'] for r in ok if r.get('matched_budget')]):.0f} mv={med([r['matvecs_total'] for r in ok if r.get('matvecs_total')]):.0f} wall={med([r['wall'] for r in v]):.1f}"
          f" |d-dense|max={max(dd) if dd else float('nan'):.1e} ferr={med([r['full_err_vs_dense'] for r in ok if 'full_err_vs_dense' in r]):.1e} probes_conv={sum(p['status']=='CONVERGED' for p in ps)}/{len(ps)} {dict(reasons)}")
# paired comparison on identical states
pairs=collections.defaultdict(dict)
for r in rows:pairs[(r['setting'],r.get('seed_index',0),r['checkpoint'],r['gamma'])][r['variant']]=r
for ref,other in (('V0_frozen','V1_noprecond'),('V0_frozen','V3_noprecond_f64'),('V0_frozen','V4_noprecond_ondrift_f64'),('V1_noprecond','V3_noprecond_f64'),('V3_noprecond_f64','V4_noprecond_ondrift_f64')):
    for field in ('delta','cheap_rho','E_task','short_gain','matched_gain','matched_budget'):
        rel=[];
        for p in pairs.values():
            a,b=p.get(ref),p.get(other)
            if a and b and a.get(field) is not None and b.get(field) is not None and a['status']==b['status']=='NUMERIC_VALID':
                rel.append(abs(a[field]-b[field])/max(abs(a[field]),1e-30))
        if rel:print(f'{ref} vs {other} {field}: n={len(rel)} rel med {np.median(rel):.1e} max {max(rel):.1e}')
