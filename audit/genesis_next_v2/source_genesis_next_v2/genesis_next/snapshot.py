"""Pure reanalysis of committed S1 snapshot files, no frozen pipeline imports."""
from __future__ import annotations
from collections import defaultdict,Counter
from pathlib import Path
import statistics
import math
from .io_utils import csv_rows,jsonl,read_json,write_json,write_csv,assert_separate,digest

def aggregate_seeds(rows, checkpoints=(1,2,3)):
    by=defaultdict(dict)
    for r in rows:
        if r.get('stage','s1')!='s1':raise ValueError('S2 leakage: this kit accepts S1 only')
        if r.get('schema')!='coarse' or r.get('state',r.get('status')) not in ('COMPLETE','NUMERIC_VALID'):continue
        ck=int(r['checkpoint_index'])
        if ck not in checkpoints:continue
        value=r.get('target_delta',r.get('delta'))
        if value in (None,''):continue
        v=float(value)
        if not math.isfinite(v):continue
        key=(r['setting_id'],str(r['seed']),float(r['gamma']))
        if ck in by[key]:raise ValueError(f'Duplicate primary checkpoint {key}/{ck}')
        by[key][ck]=v
    return [{'setting_id':s,'seed':seed,'gamma':ga,'delta':statistics.median(v.values())}
            for (s,seed,ga),v in sorted(by.items()) if set(v)==set(checkpoints)]

def reanalyze(bundle,output):
    bundle,output=Path(bundle).resolve(),Path(output).resolve();assert_separate(output,[bundle])
    pred_path=bundle/'03_SCIENTIFIC_DATA/prediction/DERIVED_predictor_feature_table.csv'
    audit_path=bundle/'04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_rows.jsonl'
    rows=csv_rows(pred_path);audit=list(jsonl(audit_path));ar={x['job_id']:x for x in audit}
    if len(ar)!=len(audit):raise ValueError('Duplicate numeric-audit job IDs')
    seedrows=aggregate_seeds(rows);lookup={(r['setting_id'],r['seed'],r['gamma']):r for r in seedrows}
    pairs=[]
    for r in seedrows:
        if r['gamma']!=.01:continue
        other=lookup.get((r['setting_id'],r['seed'],.1))
        if other:pairs.append({'setting_id':r['setting_id'],'seed':r['seed'],'delta_001':r['delta'],
                              'delta_01':other['delta'],'difference':r['delta']-other['delta']})
    baseline=[]
    for r in rows:
        if r.get('schema')!='coarse' or r.get('state')!='COMPLETE' or r['job_id'] not in ar:continue
        a=ar[r['job_id']];F=float(a['v2_F_star']);g2=10**(2*float(r['log10_grad']))
        if F<=0:continue
        baseline.append({'job_id':r['job_id'],'setting_id':r['setting_id'],'seed':r['seed'],
          'gamma':float(r['gamma']),'checkpoint_index':int(r['checkpoint_index']),
          'matched_gain_over_v2_oracle':float(r['matched_gain_over_g2'])*g2/F,
          'short_gain_over_v2_oracle':float(r['short_gain_over_g2'])*g2/F,
          'oracle_status':'RECORDED_FP32_NOT_INDEPENDENT_TRUTH'})
    coarse_a=[a for a in audit if a['schema']=='coarse']
    errors=[]
    for a in coarse_a:
        ds=[abs(a['v2_'+k]-a['ref_'+k]) for k in ('delta','E_task','E_val')
            if a.get('v2_'+k) is not None and a.get('ref_'+k) is not None]
        D=max(ds) if ds else None
        errors.append({'job_id':a['job_id'],'setting_id':a['setting'],'seed_index':a['seed_index'],
                       'checkpoint':a['checkpoint'],'gamma':a['gamma'],'reported_class':a['class'],
                       'max_metric_difference':D,'delta_error':a['v2_delta']-a['ref_delta']
                       if a.get('v2_delta') is not None and a.get('ref_delta') is not None else None})
    summary={'status':'EXPLORATORY_SNAPSHOT_ONLY','snapshot_root_name':bundle.name,
             'source_file_hashes':{str(p.relative_to(bundle)):digest(p) for p in (pred_path,audit_path)},
             'coarse_input_rows':len(rows),'audited_rows':len(audit),'audited_coarse':len(coarse_a),
             'audit_classes':dict(Counter(a['class'] for a in coarse_a)),
             'paired_seed_n':len(pairs),'pairs_positive':sum(r['difference']>0 for r in pairs),
             'paired_settings':len(set(x['setting_id'] for x in pairs)),
             'median_low_damping':statistics.median(x['delta_001'] for x in pairs) if pairs else None,
             'median_high_damping':statistics.median(x['delta_01'] for x in pairs) if pairs else None,
             'median_paired_difference':statistics.median(x['difference'] for x in pairs) if pairs else None,
             'matched_ratio_min':min(x['matched_gain_over_v2_oracle'] for x in baseline) if baseline else None,
             'matched_ratio_max':max(x['matched_gain_over_v2_oracle'] for x in baseline) if baseline else None,
             'baseline_rows_not_independent_seeds':len(baseline),
             'limitations':['S1 only; no confirmation or live status','Recorded FP32 oracle can be biased',
                            'Pooled medians descriptive, not a population estimator across settings']}
    output.mkdir(parents=True,exist_ok=True)
    write_csv(output/'seed_aggregates.csv',seedrows);write_csv(output/'paired_damping.csv',pairs)
    write_csv(output/'baseline_ratios.csv',baseline);write_csv(output/'audit_errors.csv',errors)
    write_json(output/'summary.json',summary)
    # Mechanism records have duplicated gamma/schema sweeps. Deduplicate by state.
    mpath=bundle/'03_SCIENTIFIC_DATA/mechanism/mechanism_records.jsonl';mechanism=[];seen={}
    if mpath.exists():
        for r in jsonl(mpath):
            if r['schema']!='coarse':continue
            key=(r['setting_id'],str(r['seed']),int(r['checkpoint_index']))
            m=r.get('mechanism') or {};e=m.get('exact_reference') or {}
            if key in seen:
                # The exact block is recomputed per gamma in v2. Use the first, record no new samples.
                continue
            seen[key]=True
            if e.get('status')!='DENSE_REFERENCE':continue
            for d in e['damping_sweep']:
                nn=d['GGN_null_component_fro'];hh=d['GGN_horizontal_component_fro']
                mechanism.append({'setting_id':key[0],'seed':key[1],'checkpoint':key[2],
                    'damping_absolute':d['damping'],'rank_G':e['rank_G'],'nullity_G':e['nullity_G'],
                    'null_gradient_relative':e['null_gradient_relative'],
                    'null_squared_norm_fraction_from_frozen_decomposition':nn*nn/(nn*nn+hh*hh),
                    'relative_H_G_gap':e['relative_H_G_gap'],'H_negative_count':e['H_negative_count_tolerance'],
                    'H_sign_tolerance':e.get('H_sign_tolerance'),'H_shifted_spd':d['H_shifted_spd'],
                    'pole_distance':d['pole_distance'],
                    'caution':'Threshold-defined nullspace; not new independent numerical validation'})
    write_csv(output/'mechanism_deduplicated.csv',mechanism)
    text=f'''# E0 snapshot reanalysis\n\nStatus: **EXPLORATORY; not a S1/S2 verdict**.\n\n- Paired independent-seed records: {len(pairs)}; positive damping differences: {summary['pairs_positive']}.\n- Audited coarse measurements: {len(coarse_a)}; classes: {summary['audit_classes']}.\n- Matched-CG/original FP32 oracle range: {summary['matched_ratio_min']} to {summary['matched_ratio_max']}.\n- Original v2 run and results were not read for writing or changed.\n\nSee CSV files for grouping and denominators. Do not infer optimizer speedup from quadratic gain.\n'''
    (output/'E0_REPORT.md').write_text(text,encoding='utf-8')
    return summary
