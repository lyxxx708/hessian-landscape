"""Deterministic S/M/U/P decisions. Completed code or CPU smoke is never science PASS."""
from collections import Counter
from pathlib import Path
from genesis_gpu.runtime.queue import JobStore
from genesis_gpu.runtime.atomic_io import read_json,atomic_json,file_receipt,verify_receipt,sha256_file
from genesis_gpu.study.freeze import set_state
from genesis_gpu.study.statistics import summarize_utility,summarize_structure
from genesis_gpu.science.predictor import fit_frozen_predictor,evaluate_predictor


def read_measurements(root,stage=None):
    root=Path(root);store=JobStore(root/'run_status.sqlite');records=[]
    try:
        for row in store.rows(stage):
            entry=(row.get('result') or {}).get('receipt')
            if row['kind']=='measure' and entry:
                if not verify_receipt(root,entry):raise RuntimeError('Measurement manifest corrupted: '+row['id'])
                record=read_json(root/entry['path'])
                for artifact in record['artifacts']:
                    if not verify_receipt(root,artifact):raise RuntimeError('Raw measurement artifact corrupted: '+artifact['path'])
                records.append(record)
        return records
    finally:store.close()


def flatten_utility(record):
    pv=record['provenance'];u=record['utility']
    return {'job_id':record['job_id'],'stage':pv['stage'],'setting_id':pv['setting_id'],'seed':pv['seed'],
            'checkpoint_index':pv['checkpoint_index'],'family':record['family'],'gamma':record['gamma'],
            'schema':record['schema'],'status':u['status'],'delta':u.get('delta'),'eta':u.get('eta'),
            'E_task':u.get('E_task'),'E_val':u.get('E_val'),'lambda_absolute':record['lambda_absolute']}


def adjudicate(cfg,root,stage):
    root=Path(root);store=JobStore(root/'run_status.sqlite')
    try:
        if stage not in ('s1','s2') or not store.stage_complete(stage):raise RuntimeError('Stage execution is not complete; cannot adjudicate')
        jobs=store.rows(stage);digest=store.evidence_digest(stage)
    finally:store.close()
    lock=read_json(root/'protocol-lock.json');records=read_measurements(root,stage)
    planned=Counter(r['setting_id'] for r in lock['runs'] if r['stage']==stage)
    utility=summarize_utility([flatten_utility(r) for r in records],cfg,planned)
    structure=summarize_structure(records,cfg,planned_counts=planned)
    if stage=='s1':
        predictor=fit_frozen_predictor(records,lock['protocol_sha'])
        path=root/'audit'/'predictor_frozen_s1.json';atomic_json(path,predictor)
        prediction={'status':'FROZEN_DISCOVERY_MODEL','prediction_gate_pass':False,'model_receipt':file_receipt(path,root)}
    else:
        s1=read_json(root/'audit'/'s1_adjudication.json');entry=s1['prediction']['model_receipt']
        if not verify_receipt(root,entry):raise RuntimeError('S1 predictor changed after selection freeze')
        predictor=read_json(root/entry['path'])
        if predictor['protocol_sha']!=lock['protocol_sha']:raise RuntimeError('Predictor protocol mismatch')
        prediction=evaluate_predictor(predictor,records,cfg)
    numerical_coverage={sid:{'planned_seeds':n,'completed_training_seeds':sum(j['kind']=='train' and j['state']=='COMPLETE' and j['payload']['run']['setting_id']==sid for j in jobs)} for sid,n in planned.items()}
    enough=all(v['completed_training_seeds']>=max(1,__import__('math').ceil(.8*v['planned_seeds'])) for v in numerical_coverage.values())
    enough=bool(enough and utility['conditions'] and all(c['status']=='EVALUATED' for c in utility['conditions']))
    production=cfg['profile']=='full'
    gate=production and stage=='s2' and enough and utility['utility_gate_pass'] and prediction['prediction_gate_pass'] and utility['vision_positive'] and utility['text_positive']
    mechanism_rows=[r for r in records if r.get('mechanism')]
    receipt={'schema_version':2,'stage':stage,'profile':cfg['profile'],'protocol_sha':lock['protocol_sha'],
             'execution_complete':True,'jobs_digest':digest,'counts':dict(Counter(j['state'] for j in jobs)),
             'utility':utility,'structure':structure,'prediction':prediction,
             'mechanism':{'verdict':'CONDITIONAL_DIAGNOSTICS_ONLY' if mechanism_rows else 'NOT_IDENTIFIED','measured_states':len(mechanism_rows),
                          'no_universal_gauge_or_causality_claim':True},
             'coverage':numerical_coverage,'coverage_qualified':enough,'s3_gate_pass':bool(gate),
             'verdict':'ENGINEERING_SMOKE_ONLY' if not production else ('CONFIRMATION_PENDING' if stage=='s1' else
                      'CONDITIONAL_UTILITY_SUPPORTED' if enough and utility['utility_gate_pass'] else
                      'UTILITY_NO_GO_WITHIN_TESTED_SCOPE' if enough else 'INCOMPLETE_NUMERIC_COVERAGE'),
             'scientific_complete':False,'measurement_receipts':[file_receipt(root/'measurements'/r['job_id']/'result.json',root) for r in records]}
    atomic_json(root/'audit'/f'{stage}_adjudication.json',receipt)
    set_state(root,stage.upper()+'_ADJUDICATED',scientific_complete=False)
    return receipt
