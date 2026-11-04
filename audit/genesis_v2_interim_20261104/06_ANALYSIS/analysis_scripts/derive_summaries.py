"""Derive descriptive summaries from the snapshot's own exported files. No inference and no new measurement.

Usage: python derive_summaries.py <snapshot_dir>
"""
import csv,glob,json,re,sys,collections as C,statistics as st
S=sys.argv[1]
inv=[json.loads(l) for l in open(f'{S}/02_EXECUTION/job_inventory/job_inventory.jsonl',encoding='utf-8')]
def jl(p):return [json.loads(l) for l in open(p,encoding='utf-8')]
def csvw(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
out={}
# 1. independent seed coverage: one training run (seed) is the independent unit
tr=[r for r in inv if r['kind']=='train']
cov=C.defaultdict(lambda:C.Counter())
for r in tr:cov[(r['stage'],r['family'],r['setting_id'])][r['state']]+=1
meas=C.defaultdict(lambda:C.defaultdict(C.Counter))
for r in inv:
    if r['kind']=='measure' and r['schema']=='coarse':meas[(r['stage'],r['family'],r['setting_id'])][r['seed_index']][r['state']]+=1
rows=[]
for k,c in sorted(cov.items()):
    seeds_with_valid=sum(1 for s,cc in meas[k].items() if cc.get('COMPLETE',0)>0)
    rows.append({'stage':k[0],'family':k[1],'setting_id':k[2],'planned_seeds':sum(c.values()),'training_complete':c.get('COMPLETE',0),'training_failed':c.get('FAILED',0),'training_pending':c.get('PENDING',0),
                 'seeds_with_any_complete_coarse_measurement':seeds_with_valid,
                 'coarse_measure_COMPLETE':sum(cc.get('COMPLETE',0) for cc in meas[k].values()),'coarse_measure_NUMERIC_UNRESOLVED':sum(cc.get('NUMERIC_UNRESOLVED',0) for cc in meas[k].values()),
                 'coarse_measure_BLOCKED':sum(cc.get('BLOCKED',0) for cc in meas[k].values()),'coarse_measure_PENDING_or_RUNNING':sum(cc.get('PENDING',0)+cc.get('RUNNING',0) for cc in meas[k].values())})
csvw(f'{S}/06_ANALYSIS/existing_statistics/seed_coverage_by_setting.csv',rows)
# 2. state/gamma/schema breakdown of terminal measurement outcomes
b=C.Counter((r['gamma'],r['schema'],r['tier'],r['state']) for r in inv if r['kind']=='measure' and r['state'] in('COMPLETE','NUMERIC_UNRESOLVED','BLOCKED'))
csvw(f'{S}/03_SCIENTIFIC_DATA/numerical_eligibility/outcome_counts_by_gamma_schema_tier.csv',[{'gamma':k[0],'schema':k[1],'tier':k[2],'state':k[3],'count':v} for k,v in sorted(b.items(),key=str)])
# 3. audit coverage against the snapshot, and false-valid cases
au=jl(f'{S}/04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_rows.jsonl')
audited={r['job_id'] for r in au}
complete=[r for r in inv if r['kind']=='measure' and r['state']=='COMPLETE']
unaud=[r['job_id'] for r in complete if r['job_id'] not in audited]
json.dump({'snapshot_complete_measurements':len(complete),'audited_rows':len(au),'audited_in_snapshot':len(audited&{r['job_id'] for r in complete}),'complete_not_audited':len(unaud),
           'complete_not_audited_job_ids':unaud,'note':'audit pass predates snapshot; not rerun by this packaging task (owner instruction)'},open(f'{S}/04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_coverage_vs_snapshot.json','w'),indent=1)
with open(f'{S}/04_NUMERICAL_AUDIT/false_valid_cases/false_valid_cases.jsonl','w',encoding='utf-8',newline='\n') as f:
    for r in au:
        if r['class']!='AGREE':f.write(json.dumps(r,sort_keys=True)+'\n')
cls=C.Counter(r['class'] for r in au)
pairs=C.defaultdict(dict)
for r in au:pairs[(r['setting'],r['seed_index'],r['checkpoint'],r['gamma'])][r['schema']]=r
ident=sum(1 for v in pairs.values() if len(v)==2 and v['coarse']['v2_delta']==v['fine']['v2_delta'])
state_err={}
for r in au:state_err[(r['setting'],r['seed_index'],r['checkpoint'])]={k:r[k] for k in ('grad_rel_err','grad_cos','grad_norm_fp64','grad_norm_fp32_cpu','grad_norm_v2_gpu')}
csvw(f'{S}/04_NUMERICAL_AUDIT/false_valid_cases/per_state_gradient_error.csv',[{'setting':k[0],'seed_index':k[1],'checkpoint':k[2],**v} for k,v in sorted(state_err.items())])
out['audit']={'rows':len(au),'classes':dict(cls),'distinct_measurements':len(pairs),'coarse_fine_identical_v2_delta_pairs':ident}
# 4. v2.1 DLN comparison summary
rows=[]
for p in sorted(glob.glob(f'{S}/05_V21_QUALIFICATION/dln_comparison/dln_dln_*.jsonl')):rows+=jl(p)
sm=[]
for g in (0.001,0.01,0.1):
    for v in sorted({r['variant'] for r in rows}):
        R=[r for r in rows if r['variant']==v and abs(r['gamma']-g)<1e-12];ok=[r for r in R if r['status']=='NUMERIC_VALID']
        E=[abs(r['delta']-r['dense_delta']) for r in ok if r.get('dense_delta') is not None]
        P=[p for r in R for p in (r.get('probe_solves') or [])]
        def med(k):
            x=[r[k] for r in R if r.get(k) is not None];return st.median(x) if x else None
        sm.append({'gamma':g,'variant':v,'cases':len(R),'numeric_valid':len(ok),'probe_converged':sum(p['status']=='CONVERGED' for p in P),'probe_total':len(P),'max_abs_delta_error_vs_dense':max(E) if E else None,
                   'median_full_iterations':med('full_it'),'median_tight_iterations':med('tight_it'),'median_wall_s':med('wall'),'median_matvecs_total':med('matvecs_total'),'median_matched_budget':med('matched_budget')})
csvw(f'{S}/05_V21_QUALIFICATION/dln_comparison/dln_variant_summary.csv',sm)
out['dln_rows']=len(rows)
# 5. coarse/fine redundancy evidence from the executed source
ev=[]
for fn in ('dln','mlp'):
    t=open(f'{S}/07_SOURCE/executed_source/genesis_gpu/models/{fn}.py',encoding='utf-8').read().splitlines()
    i=next(i for i,l in enumerate(t) if 'def group_for' in l);ev.append((fn,i+1,t[i],t[i+1]))
sched=[r for r in inv if r['kind']=='measure']
redund=sum(1 for r in sched if r['family'] in('dln','mlp') and r['schema']=='fine' and r['stage']=='s1')
tot=sum(1 for r in sched if r['stage']=='s1')
filt=[]
for fn in ('study/statistics.py','science/predictor.py'):
    for n,l in enumerate(open(f'{S}/07_SOURCE/executed_source/genesis_gpu/{fn}',encoding='utf-8').read().splitlines(),1):
        if "'coarse'" in l and 'schema' in l:filt.append((fn,n,l.strip()))
with open(f'{S}/04_NUMERICAL_AUDIT/reproducibility/coarse_fine_redundancy_evidence.md','w',encoding='utf-8',newline='\n') as f:
    f.write('# Coarse/fine grouping redundancy: code and count evidence\n\nGenerated by `derive_summaries.py` from files in this snapshot.\n\n## `group_for` ignores `schema` (DLN, MLP)\n\n')
    for fn,n,a,b2 in ev:f.write(f'- `genesis_gpu/models/{fn}.py:{n}`: `{a.strip()}` then `{b2.strip()}`\n')
    f.write('\nResNet and Transformer have separate `group_for` implementations that were not reviewed for this note.\n\n## Statistics filter to coarse\n\n')
    for fn,n,l in filt:f.write(f'- `genesis_gpu/{fn}:{n}`: `{l}`\n')
    f.write(f'\n## Count in the job inventory\n\nS1 measurement jobs in the inventory: {tot}. S1 DLN and MLP jobs with `schema=fine`: {redund}.\n')
    f.write(f'\nAudited DLN measurements: {len(pairs)} distinct (setting, seed, checkpoint, gamma); coarse and fine v2 delta identical in {ident} of them.\n')
out['coarse_fine']={'s1_jobs':tot,'dln_mlp_fine':redund,'identical_pairs':ident,'pairs':len(pairs)}
print(json.dumps(out,indent=1))
