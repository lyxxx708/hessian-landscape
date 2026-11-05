from __future__ import annotations
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from .io_utils import read_json,write_json,write_csv

def summarize_rows(rows,bootstrap=2000,seed=20261105):
    rng=np.random.default_rng(seed);by=defaultdict(list)
    for r in rows:
        if r.get('status')=='QUALIFIED':by[(r['setting_id'],float(r['gamma']))].append(r)
    output=[]
    for (sid,ga),rs in sorted(by.items()):
        seeds=defaultdict(dict)
        for r in rs:
            s=str(r['seed']);ck=int(r['checkpoint'])
            if ck in seeds[s]:raise ValueError('Duplicate state/gamma in analysis')
            seeds[s][ck]=r
        eligible={s:cs for s,cs in seeds.items() if set(cs)=={1,3}}
        summary={'setting_id':sid,'gamma':ga,'independent_seed_n':len(eligible),'measurement_n':len(rs),
                 'inference':'EXPLORATORY_SEED_CLUSTER; no p-value or confirmation'}
        for metric in ('delta','matched_gain_ratio','cg8_gain_ratio'):
            vals=[np.median([cs[k][metric] for k in (1,3)]) for cs in eligible.values()
                  if all(cs[k].get(metric) is not None for k in (1,3))]
            if vals:
                v=np.asarray(vals);boot=np.median(v[rng.integers(0,len(v),(bootstrap,len(v)))],axis=1)
                summary[metric+'_median']=float(np.median(v));summary[metric+'_seed_n']=len(v)
                # With <4 seeds this is a descriptive point estimate only.
                summary[metric+'_ci_low']=float(np.quantile(boot,.025)) if len(v)>=4 else None
                summary[metric+'_ci_high']=float(np.quantile(boot,.975)) if len(v)>=4 else None
        output.append(summary)
    return output

def report(output):
    output=Path(output);lock=read_json(output/'FOLLOWUP_LOCK.json');results=[];rows=[]
    for p in sorted((output/'results').glob('*.json')):
        r=read_json(p)
        if r.get('freeze_sha')!=lock['freeze_sha']:raise ValueError('Foreign result in follow-up root')
        results.append(r)
        for c in r.get('conditions',[]):
            comparisons=c.get('comparators',[]);cg8=next((x for x in comparisons if x['name']=='cg_8'),None)
            matched=next((x for x in comparisons if x['name']=='matched_matvec_cg'),None)
            rows.append({'state_id':r['state_id'],'setting_id':r['setting_id'],'family':r['family'],
              'seed':str(r['seed']),'checkpoint':r['checkpoint'],'gamma':c['gamma'],'status':c['status'],
              'delta':c.get('delta'),'F_star':c.get('F_star'),'absolute_block_gain_gap':c.get('absolute_block_gain_gap'),
              'matched_gain_ratio':matched.get('gain_ratio') if matched else None,
              'cg8_gain_ratio':cg8.get('gain_ratio') if cg8 else None,
              'reference_class':c.get('reference_class')})
    s=summarize_rows(rows,lock['config']['bootstrap_replicates'],lock['config']['bootstrap_seed'])
    folder=output/'analysis';write_csv(folder/'condition_rows.csv',rows);write_csv(folder/'seed_summary.csv',s)
    count=Counter(r['status'] for r in results);complete=len(results)==len(lock['plan']['states'])
    write_json(folder/'coverage.json',{'planned_states':lock['plan']['state_count'],'state_records':len(results),
                                     'state_statuses':dict(count),'execution_records_complete':complete,
                                     'scientific_confirmation':False})
    text='# GENESIS NEXT — follow-up report\n\nThis is S1 exploratory remeasurement, not a v2 verdict or independent confirmation.\n\n'
    text+=f"Planned states: {lock['plan']['state_count']}; recorded states: {len(results)}; statuses: {dict(count)}.\n\n"
    text+='Every missing, timed-out, rejected-reference or unavailable state remains in the planned denominator.\n'
    text+='Numeric qualification is per condition. A state finishing is not equivalent to all conditions passing.\n'
    text+='Use seed_summary.csv for within-setting estimates; no pooled-seed population claim across architectures.\n'
    (folder/'REPORT.md').write_text(text,encoding='utf-8')
    return {'state_statuses':dict(count),'planned_states':lock['plan']['state_count'],'conditions':len(rows),
            'summary_rows':len(s),'status':'EXPLORATORY_PARTIAL' if not complete else 'EXPLORATORY_EXECUTION_RECORDED'}
