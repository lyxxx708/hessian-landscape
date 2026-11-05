"""Independent recomputation of main claims from results/per_state/*.json only (no CSV, no summaries).
Usage: python recompute_from_raw.py [package_dir]   (needs numpy only)"""
import json,sys
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
res=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((root/'results/per_state').glob('*.json'))]
cfg=json.loads((root/'results/FOLLOWUP_LOCK.json').read_text())['config']
conds=[(r,c) for r in res for c in r['conditions']]
print('states',len(res),'conditions',len(conds))
# C1
ok=0
for r,c in conds:
    g=r['reference_gradient_crosscheck']<=cfg['operator_crosscheck_rtol'] and max(r['operator_crosscheck_errors'])<=cfg['operator_crosscheck_rtol']
    g&=r['dense_gradient_relative_error']<=cfg['operator_crosscheck_rtol'] and c['full_direction_relative_error']<=cfg['reference_solution_rtol']
    g&=c['dense_delta_error']<=cfg['reference_delta_atol'] and c['full_solve']['converged'] and c['block_solve']['converged'] and -1e-6<=c['delta']<=1+1e-6 and c['F_star']>0
    ok+=bool(g)
print('C1 recomputed qualified',ok,'/',len(conds),'; recorded QUALIFIED',sum(c['status']=='QUALIFIED' for r,c in conds))
# C2: independent delta check from F values, CG vs block
bad=0;ratios=[];ks=[]
for r,c in conds:
    if abs((1-c['F_block']/c['F_star'])-c['delta'])>1e-12:bad+=1
    tgt=1-c['delta'];hit=None
    for x in c['comparators']:
        if x['name'].startswith('cg_') and x['gain_ratio']>=tgt:hit=x;break
    if hit:ratios.append(hit['solve_wall_vs_block']);ks.append(int(hit['name'][3:]))
print('C2 delta=1-Fb/F* mismatches',bad,'; CG matches block in',len(ks),'/',len(conds),'; matching-budget wall ratio median/max',np.median(ratios),max(ratios),'; median grid k',np.median(ks))
# C3
g=[c['geometry'][1] for r,c in conds]
print('C3 null_energy min/median',min(x['null_energy_fraction'] for x in g),np.median([x['null_energy_fraction'] for x in g]),'grad_null max',max(x['gradient_null_fraction'] for x in g),'eff gain dirs median',np.median([x['effective_gain_directions'] for x in g]))
# C4
a=[c['e4_delta_attribution'] for r,c in conds]
e=np.array([abs(x['v2_total_error']) for x in a if 'v2_total_error' in x])
print('C4 v2 valid rows',len(e),'median abs err',np.median(e),'rows >1e-3',int((e>1e-3).sum()),'v2 unresolved yet FP64 valid',sum(x['v2_recorded_status']!='NUMERIC_VALID' for x in a))
# C5
nb=sum(c['block_ray_loss']['validation_gain']<0 for r,c in conds);nf=sum(c['full_loss']['validation_gain']<0 for r,c in conds)
print('C5 negative val gain: block',nb,'/',len(conds),'full',nf,'/',len(conds),'; independent seeds',len({(r['setting_id'],r['seed']) for r in res}))
# C8
print('C8 executed states',len(res),'of 80; executed conditions',len(conds),'of 240')
