"""Post-measurement tables and seed-clustered statistics. Reads only committed results/ of the frozen NEXT v2 root.
Analysis plan is in NEXT_V2_PROTOCOL_LOCK.json (written before data)."""
import csv,json,sys,hashlib
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0,r'E:\GENESIS\worktrees\genesis-next-v2')
from genesis_next.ledger import condition_ledger
from genesis_next.cli import source_ready

O=Path(r'E:\GENESIS\runs\genesis_next_v2')
lock=json.loads((O/'FOLLOWUP_LOCK.json').read_text(encoding='utf-8'))
results={}
for p in sorted((O/'results').glob('*.json')):
    r=json.loads(p.read_text(encoding='utf-8'))
    assert r['freeze_sha']==lock['freeze_sha']
    results[r['state_id']]=r
ready={s['state_id']:source_ready(lock,s) for s in lock['plan']['states']}
running=set()
hb=O/'DRIVER_HEARTBEAT.json'
if hb.exists():
    running=set(json.loads(hb.read_text()).get('running',{}))
ledger=condition_ledger(lock,results,ready,running)
def W(name,rows):
    rows=list(rows)
    if not rows:
        (O/name).write_text('NOT_PRODUCED\n',encoding='utf-8');return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (O/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

W('EXPERIMENT_INVENTORY.csv',ledger)
W('FAILURES_AND_CENSORING.csv',[r for r in ledger if r['status']!='NUMERIC_VALID'])

qual=[];sci=[];cgc=[];mech=[];e4=[]
by_state={s['state_id']:s for s in lock['plan']['states']}
for sid,r in results.items():
    st=by_state[sid];base={'state_id':sid,'setting_id':r.get('setting_id'),'family':r.get('family'),'seed_index':st['run']['seed_index'],
        'seed':str(r.get('seed')),'checkpoint':r.get('checkpoint'),'source_sha_protocol':lock['inputs']['protocol_lock_sha256'][:12]}
    if r.get('status')=='EXECUTED':
        e4.append({**base,'record':'state_precision','input_quantization':r.get('input_quantization_control'),'precision':r.get('precision'),
                   'reference_gradient_crosscheck':r.get('reference_gradient_crosscheck'),'operator_crosscheck_errors':r.get('operator_crosscheck_errors'),
                   'dense_gradient_relative_error':r.get('dense_gradient_relative_error')})
    for c in r.get('conditions',[]):
        g=c['gamma']
        qual.append({**base,'gamma':g,'status':c['status'],'reason':c.get('reason'),'reference_class':c.get('reference_class'),
            'full_converged':c.get('full_solve',{}).get('converged'),'full_true_residual':c.get('full_solve',{}).get('relative_true_residual'),
            'block_converged':c.get('block_solve',{}).get('converged'),'full_direction_relative_error':c.get('full_direction_relative_error'),
            'dense_delta_error':c.get('dense_delta_error'),'grad_crosscheck':r.get('reference_gradient_crosscheck'),
            'operator_crosscheck_max':max(r['operator_crosscheck_errors']) if r.get('operator_crosscheck_errors') else None,
            'v2_status':(c.get('original_v2_read_only') or {}).get('utility_status')})
        if c['status']!='QUALIFIED':continue
        comp={x['name']:x for x in c['comparators']}
        bl=c['block_ray_loss'];fl=c['full_loss']
        gt=c['geometry'][1];hs=r['hessian'][1] if r.get('hessian') else {}
        row={**base,'gamma':g,'delta':c['delta'],'F_star':c['F_star'],'F_block':c['F_block'],'abs_gain_gap':c['absolute_block_gain_gap'],
          'block_gain_ratio':1-c['delta'],'full_matvecs':c['full_solve']['matvecs'],'block_matvecs':c['block_solve']['matvecs'],
          'block_solve_plus_Q_wall_s':c['block_solve_plus_Q_wall'],'full_cg_wall_s':c['full_solve']['wall_seconds'],
          'gradient_norm':c['gradient_norm'],'train_loss':bl['train_loss'],
          'block_train_gain':bl['train_gain'],'block_val_gain':bl['validation_gain'],'full_train_gain':fl['train_gain'],'full_val_gain':fl['validation_gain'],
          'block_gain_above_roundoff':bl['gain_above_roundoff_heuristic'],
          'first_tested_cg_budget_ge99':c['first_tested_cg_budget_ge99'],
          'original_v2_delta':(c.get('original_v2_read_only') or {}).get('delta'),'original_v2_status':(c.get('original_v2_read_only') or {}).get('utility_status'),
          'rank':gt['rank'],'nullity':gt['nullity'],'null_energy_fraction':gt['null_energy_fraction'],'gradient_null_fraction':gt['gradient_null_fraction'],
          'inverse_offdiag_fraction':gt['inverse_offdiag_fraction'],'null_offdiag_fraction':gt['null_offdiag_fraction'],'active_offdiag_fraction':gt['active_offdiag_fraction'],
          'gradient_weighted_n99':gt['gradient_weighted_n99'],'effective_gain_directions':gt['effective_gain_directions'],
          'H_G_rel_fro':hs.get('relative_H_G_fro'),'neg_count':hs.get('negative_certified_count'),'neg_mass_fraction':hs.get('negative_mass_fraction')}
        # CG that first matches the Block gain (grid-censored)
        tgt=1-c['delta'];match=None
        for k in (1,2,4,8,16,32,64):
            x=comp.get(f'cg_{k}')
            if x and x['gain_ratio']>=tgt:match=(k,x);break
        row['cg_grid_k_matching_block_gain']=match[0] if match else None
        row['cg_matching_matvecs']=match[1]['solve']['matvecs'] if match else None
        row['cg_matching_wall_ratio_vs_block']=match[1]['solve_wall_vs_block'] if match else None
        row['cg_matching_censoring']='OBSERVED_GRID_CROSSING' if match else 'NOT_REACHED_BY_CG64'
        m=comp.get('matched_matvec_cg')
        row['matched_matvec_budget']=c['matched_matvec_budget'];row['matched_gain_ratio']=m['gain_ratio'] if m else None
        row['matched_wall_ratio_vs_block']=m['solve_wall_vs_block'] if m else None
        sci.append(row)
        for x in c['comparators']:
            cgc.append({**base,'gamma':g,'comparator':x['name'],'gain_ratio':x['gain_ratio'],'block_gain_ratio':tgt,'beats_or_equals_block':x['gain_ratio']>=tgt,
              'matvecs':x['solve']['matvecs'],'iterations':x['solve']['iterations'],'true_residual':x['solve']['relative_true_residual'],
              'solve_wall_s':x['solve']['wall_seconds'],'solve_wall_vs_block':x['solve_wall_vs_block'],'end_to_end_wall_s':x['end_to_end_wall'],
              'train_gain':x['line_search']['train_gain'],'val_gain':x['line_search']['validation_gain'],'budget_enforced':x['matvec_budget_enforced'],
              'wall_time_equivalence_claimed':False,'block_matvecs':c['block_solve']['matvecs']})
        mech.append({**base,'gamma':g,'geometry_by_rank_tolerance':c['geometry'],'hessian_by_rank_tolerance':r.get('hessian'),'gauge':c.get('gauge')})
        if 'e4_delta_attribution' in c:e4.append({**base,'gamma':g,'record':'delta_attribution',**c['e4_delta_attribution']})
        else:e4.append({**base,'gamma':g,'record':'delta_attribution','status':'NOT_EVALUABLE_NO_DENSE_REFERENCE'})
W('NUMERICAL_QUALIFICATION.csv',qual);W('SCIENTIFIC_RESULTS.csv',sci);W('CG_COST_COMPARISON.csv',cgc)
def J(name,rows):
    rows=list(rows)
    with (O/name).open('w',encoding='utf-8') as f:
        if not rows:f.write('')
        for r in rows:f.write(json.dumps(r,ensure_ascii=False,default=str)+'\n')
    if not rows:(O/name).write_text('NOT_PRODUCED\n',encoding='utf-8')
J('STRUCTURE_MECHANISM_RESULTS.jsonl',mech);J('NUMERICAL_ERROR_AUDIT.jsonl',e4)

# ---- seed-clustered statistics (descriptive, no p-values)
rng=np.random.default_rng(lock['config']['bootstrap_seed'])
def seedmed(rows,key):
    per=defaultdict(list)
    for r in rows:
        if r.get(key) is not None:per[r['seed']].append(float(r[key]))
    return [float(np.median(v)) for v in per.values()]
def boot(v):
    v=np.asarray(v)
    if len(v)<4:return (None,None)
    b=np.median(v[rng.integers(0,len(v),(2000,len(v)))],axis=1);return (float(np.quantile(b,.025)),float(np.quantile(b,.975)))
summ=[];grp=defaultdict(list)
for r in sci:grp[(r['setting_id'],r['gamma'])].append(r)
keys=['delta','abs_gain_gap','null_energy_fraction','gradient_null_fraction','inverse_offdiag_fraction','active_offdiag_fraction','cg_grid_k_matching_block_gain','cg_matching_wall_ratio_vs_block','matched_wall_ratio_vs_block','block_val_gain','full_val_gain','full_matvecs','block_matvecs','nullity']
for (sid,g),rs in sorted(grp.items()):
    row={'setting_id':sid,'gamma':g,'independent_seed_n':len({r['seed'] for r in rs}),'measurement_n':len(rs)}
    for k in keys:
        v=seedmed(rs,k)
        if v:
            lo,hi=boot(v);row[k+'_median']=float(np.median(v));row[k+'_ci_low']=lo;row[k+'_ci_high']=hi
    row['cg_never_matches_block_n']=sum(r['cg_grid_k_matching_block_gain'] is None for r in rs)
    summ.append(row)
W('SEED_SUMMARY.csv',summ)
from scipy.stats import spearmanr
corr=[]
def rho(rows,x,y):
    a=[(r[x],r[y]) for r in rows if r.get(x) is not None and r.get(y) is not None]
    if len(a)<5:return None
    xs,ys=zip(*a)
    if len(set(xs))<2 or len(set(ys))<2:return None
    return float(spearmanr(xs,ys)[0])
pairs=[('inverse_offdiag_fraction','delta'),('active_offdiag_fraction','delta'),('null_energy_fraction','delta'),('gradient_null_fraction','delta'),('delta','cg_grid_k_matching_block_gain'),('delta','abs_gain_gap')]
for x,y in pairs:
    corr.append({'scope':'pooled_all_conditions','x':x,'y':y,'spearman':rho(sci,x,y),'n':len(sci),'note':'non-independent (seeds/ckpts/gammas pooled): descriptive'})
    for g in (0.001,0.01,0.1):
        rs=[r for r in sci if r['gamma']==g]
        corr.append({'scope':f'gamma={g}','x':x,'y':y,'spearman':rho(rs,x,y),'n':len(rs),'note':'non-independent: descriptive'})
W('STRUCTURE_UTILITY_ASSOCIATIONS.csv',corr)
counts=defaultdict(int)
for r in ledger:counts[r['status']]+=1
(O/'COVERAGE.json').write_text(json.dumps({'planned_conditions':len(ledger),'by_status':dict(counts),'states_with_result':len(results),
   'states_source_ready':sum(ready.values())},indent=2),encoding='utf-8')
print(dict(counts),len(sci),len(results))
