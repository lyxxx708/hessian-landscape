"""Prespecified seed-cluster inference; repeated checkpoints never multiply n."""
from collections import defaultdict
import math
import numpy as np
from scipy.stats import binomtest
from genesis_gpu.study.design import seed_for


def bootstrap_median(values,replicates=2000,seed=7,alpha=.05):
    values=np.asarray(values,dtype=float)
    if not len(values) or not np.isfinite(values).all():return None
    rng=np.random.default_rng(seed);draw=np.median(values[rng.integers(0,len(values),(replicates,len(values)))],axis=1)
    return {'median':float(np.median(values)),'interval':np.quantile(draw,[alpha/2,1-alpha/2]).tolist(),'n':len(values),
            'method':'percentile bootstrap over independent training-seed aggregates; finite-sample approximate'}


def holm(pvalues):
    ps=np.asarray(pvalues,dtype=float)
    if np.any(~np.isfinite(ps)) or np.any((ps<0)|(ps>1)):raise ValueError('Invalid p-values')
    order=np.argsort(ps,kind='stable');adjusted=np.empty_like(ps);last=0.
    for rank,idx in enumerate(order):last=max(last,min(1.,(len(ps)-rank)*ps[idx]));adjusted[idx]=last
    return adjusted.tolist()


def summarize_utility(rows,cfg,planned_counts):
    stat=cfg['statistics'];conditions=[]
    by=defaultdict(list)
    for row in rows:
        if row.get('schema')=='coarse' and row.get('checkpoint_index') in (1,2,3):by[row['setting_id']].append(row)
    for sid,nplanned in planned_counts.items():
        selected=by.get(sid,[]);family=next((r['family'] for r in selected),'unknown');gammas=[];seed_union=set()
        for gamma in cfg['damping_ratios']:
            repeated=defaultdict(dict)
            for r in selected:
                if math.isclose(r['gamma'],gamma,rel_tol=1e-9) and r.get('status')=='NUMERIC_VALID' and r.get('delta') is not None and math.isfinite(r['delta']):
                    if r['checkpoint_index'] in repeated[r['seed']]:raise ValueError('Duplicate seed/checkpoint/estimand row')
                    repeated[r['seed']][r['checkpoint_index']]=r['delta']
            # Complete middle/middle/end primary aggregation; no hidden within-seed endpoint selection.
            aggregates={seed:float(np.median(list(v.values()))) for seed,v in repeated.items() if set(v)=={1,2,3}}
            vals=list(aggregates.values());seed_union.update(aggregates)
            sufficient=len(vals)>=max(2,math.ceil(nplanned*stat['min_eligible_fraction']))
            ci=bootstrap_median(vals,stat['bootstrap'],seed_for('BOOTSTRAP',sid,gamma)%2**32,stat['alpha']) if vals else None
            p=binomtest(sum(v>stat['delta_lower'] for v in vals),len(vals),.5,alternative='greater').pvalue if sufficient else 1.
            passed=bool(sufficient and ci['median']>=stat['delta_median'] and ci['interval'][0]>stat['delta_lower'])
            gammas.append({'gamma':gamma,'n_valid_seeds':len(vals),'n_planned_seeds':nplanned,'seed_values':{str(k):v for k,v in aggregates.items()},
                           'summary':ci,'p_sign_above_floor':float(p),'effect_gate':passed})
        # Intersection-union partial conjunction: >=2 of K dampings, without cherry-picked min p.
        ordered=sorted(g['p_sign_above_floor'] for g in gammas)
        need=min(2,len(ordered));p_partial=min(1.,(len(ordered)-need+1)*ordered[need-1]) if ordered else 1.
        sufficient=sum(g['n_valid_seeds']>=max(2,math.ceil(nplanned*stat['min_eligible_fraction'])) for g in gammas)>=need
        conditions.append({'setting_id':sid,'family':family,'independent_seed_n':len(seed_union),'planned_seed_n':nplanned,
                           'by_gamma':gammas,'partial_conjunction_p':p_partial,'required_dampings':need,
                           'status':'EVALUATED' if sufficient else 'INSUFFICIENT_VALID_SEEDS',
                           'effect_gate':sum(g['effect_gate'] for g in gammas)>=need,'pass':False})
    adjusted=holm([c['partial_conjunction_p'] for c in conditions]) if conditions else []
    for c,p in zip(conditions,adjusted):c['holm_p']=p;c['pass']=c['effect_gate'] and p<stat['alpha']
    positive=[c for c in conditions if c['pass']]
    return {'conditions':conditions,'utility_gate_pass':len(positive)>=2 and any(c['family']!='dln' for c in positive),
            'vision_positive':any(c['pass'] and c['family'] in ('mlp','resnet') for c in conditions),
            'text_positive':any(c['pass'] and c['family']=='transformer' for c in conditions),
            'independent_unit':'training seed cluster; median of checkpoints 1/2/3 at fixed gamma',
            'multiple_testing':'partial conjunction >=2 of K damping tests, then Holm across predeclared settings',
            'not_universal_law':True}


def summarize_structure(records,cfg,planned_counts=None):
    from scipy.stats import combine_pvalues
    groups=defaultdict(list);planned_counts=planned_counts or {}
    for record in records:
        p=record['provenance'];s=record.get('structure')
        if record['schema']!='coarse' or p['checkpoint_index']!=3 or not s:continue
        groups[(p['setting_id'],record['gamma'])].append(record)
    output=[];stat=cfg['statistics']
    for (sid,gamma),recs in sorted(groups.items()):
        qualified=[];seen=set()
        for r in recs:
            s=r['structure'];p=s.get('raw_profile') or {};seed=r['provenance']['seed']
            if seed in seen:raise ValueError('Duplicate structural primary record for seed/gamma')
            seen.add(seed)
            if s['status']=='NUMERIC_VALID' and p.get('tail_status')=='ELIGIBLE':qualified.append((r,p))
        amps=[p['tail_amplitude'] for _,p in qualified];cvs=[p['tail_cv'] for _,p in qualified]
        nplanned=planned_counts.get(sid,len(recs));coverage=len(qualified)>=max(2,math.ceil(nplanned*stat['min_eligible_fraction']))
        aci=bootstrap_median(amps,stat['bootstrap']) if amps else None;cci=bootstrap_median(cvs,stat['bootstrap']) if cvs else None
        generic=bool(coverage and aci['interval'][0]>=stat['tail_amplitude'] and cci['interval'][1]<=stat['tail_cv'])
        null_ps=[r['structure']['order_null']['p_flatness'] for r,p in qualified if r['structure'].get('order_null',{}).get('p_flatness') is not None]
        order_p=float(combine_pvalues(null_ps,method='fisher').pvalue) if coverage and null_ps else 1.
        output.append({'setting_id':sid,'gamma':gamma,'family':recs[0].get('family','unknown'),
                       'independent_seed_n':len(qualified),'planned_seed_n':nplanned,'records_attempted':len(recs),
                       'coverage_qualified':coverage,'tail_amplitude':aci,'tail_cv':cci,
                       'generic_flat_tail_candidate':generic,'order_null_pvalues':null_ps,'combined_order_null_p':order_p,
                       'status':'ESTIMATED_CONDITIONAL' if coverage else 'INSUFFICIENT_VALID_SEEDS_OR_SHORT_DEPTH'})
    adjusted=holm([r['combined_order_null_p'] for r in output]) if output else []
    for r,p in zip(output,adjusted):r['holm_order_p']=p;r['order_specific_signal']=r['generic_flat_tail_candidate'] and p<stat['alpha']
    per_setting=defaultdict(list)
    for r in output:per_setting[r['setting_id']].append(r)
    positives=[sid for sid,rs in per_setting.items() if sum(r['order_specific_signal'] for r in rs)>=2]
    generic=any(sum(r['generic_flat_tail_candidate'] for r in rs)>=2 for rs in per_setting.values())
    status='STRUCTURE_CONFIRMED_CONDITIONAL' if positives else 'GENERIC_NONLOCAL_ONLY' if generic else 'NO_QUALIFIED_STRUCTURAL_SUPPORT'
    return {'conditions':output,'verdict':status,'structure_gate_pass':bool(positives),'confirmed_settings':positives,
            'architecture_specific_confirmation':bool(positives),'infinite_depth_claim':False,
            'depth_extrapolation_status':'NOT_TESTED_BY_DEFAULT_S2_ANCHORS; observed depths overlap S1, no new-depth claim',
            'limitation':'Independent-seed, finite-depth conditional results only. Fisher combination assumes independent training-seed null tests; Holm controls reported setting/damping tests.'}
