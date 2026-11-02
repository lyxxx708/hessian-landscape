"""Reports derive from verified receipts; no LLM, invented tables or positive-result bias."""
from pathlib import Path
import csv
import json
import html
import shutil
import math
import numpy as np
import pandas as pd
from genesis_gpu.runtime.atomic_io import atomic_json,atomic_bytes,read_json,file_receipt,sha256_file
from genesis_gpu.runtime.queue import JobStore
from genesis_gpu.study.adjudication import read_measurements,flatten_utility
from genesis_gpu.study.freeze import set_state


def write_table(root,name,rows):
    root=Path(root);table=root/'tables'/name
    table.parent.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(rows)
    for col in df.columns:
        if any(isinstance(x,(list,dict)) for x in df[col]):df[col]=df[col].map(lambda x:json.dumps(x,sort_keys=True) if isinstance(x,(list,dict)) else x)
    csv_path=table.with_suffix('.csv');atomic_bytes(csv_path,df.to_csv(index=False).encode())
    receipt={'csv':file_receipt(csv_path,root),'parquet':None}
    try:
        import pyarrow
        parquet=table.with_suffix('.parquet');temporary=parquet.with_suffix('.parquet.tmp')
        df.to_parquet(temporary,index=False,engine='pyarrow');temporary.replace(parquet)
        receipt['parquet']=file_receipt(parquet,root)
    except ImportError:receipt['parquet_status']='PYARROW_NOT_INSTALLED; CSV is canonical, no file mislabeled as Parquet'
    return receipt


def _markdown_table(rows,columns):
    if not rows:return '_No recorded rows._\n'
    header='| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'
    def value(v):
        if v is None:return 'N/A'
        if isinstance(v,float):return f'{v:.6g}'
        return str(v).replace('|','\\|').replace('\n',' ')
    return header+''.join('| '+' | '.join(value(row.get(c)) for c in columns)+' |\n' for row in rows)


def generate_figures(root,records):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(root);(root/'figures').mkdir(parents=True,exist_ok=True);figures=[]
    for family in sorted(set(r['family'] for r in records)):
        selected=[r for r in records if r['family']==family and r['schema']=='coarse']
        curves=[r for r in selected if r.get('structure',{} ) and (r['structure'].get('raw_profile') or {}).get('normalized_element_rms')]
        if curves:
            fig,ax=plt.subplots(figsize=(8,5))
            for record in curves[:36]:
                p=record['provenance'];c=record['structure']['raw_profile']['normalized_element_rms']
                ax.plot(range(len(c)),c,alpha=.45,label=f"{p['setting_id']} seed{p['seed_index']} γ={record['gamma']}" if len(curves)<=8 else None)
            ax.set(xlabel='Layer-group distance',ylabel='Per-element RMS / diagonal RMS',title=f'{family}: all reported bins (conditional estimates)')
            if len(curves)<=8:ax.legend(fontsize=6)
            fig.tight_layout();path=root/'figures'/f'{family}_distance.png';fig.savefig(path,dpi=160);plt.close(fig);figures.append(file_receipt(path,root))
        valid=[r for r in selected if r['utility'].get('status')=='NUMERIC_VALID' and r['utility'].get('delta') is not None]
        if valid:
            fig,ax=plt.subplots(figsize=(8,5));ax.scatter([r['gamma'] for r in valid],[r['utility']['delta'] for r in valid],alpha=.5)
            ax.set(xscale='log',xlabel='Relative damping γ',ylabel='Best-ray block-GGN regret Δ',title=f'{family}: measured states, not independent rows')
            fig.tight_layout();path=root/'figures'/f'{family}_utility.png';fig.savefig(path,dpi=160);plt.close(fig);figures.append(file_receipt(path,root))
    return figures


def generate_report(cfg,root):
    root=Path(root);(root/'reports').mkdir(parents=True,exist_ok=True)
    lock=read_json(root/'protocol-lock.json');store=JobStore(root/'run_status.sqlite')
    try:
        jobs=store.rows();stage_complete={s:store.stage_complete(s) for s in ('s1','s2')};counts=store.counts();digests={s:store.evidence_digest(s) for s in ('s1','s2')}
    finally:store.close()
    errors=[]
    if 'source' in lock:
        from genesis_gpu.study.freeze import verify_lock
        try: verify_lock(cfg,root)
        except Exception as exc: errors.append('Frozen execution identity invalid: '+repr(exc))
    try:records=read_measurements(root)
    except Exception as exc:records=[];errors.append('Cannot trust recorded measurements: '+repr(exc))
    qa_path=root/'audit'/'INDEPENDENT_VERIFIER_RECEIPT.json';qa=read_json(qa_path) if qa_path.exists() else {'status':'NOT_RUN','errors':['Independent QA not run']}
    decisions={s:read_json(root/'audit'/f'{s}_adjudication.json') if (root/'audit'/f'{s}_adjudication.json').exists() else None for s in ('s1','s2')}
    for stage in ('s1','s2'):
        if qa.get('jobs_digest',{}).get(stage)!=digests[stage]:errors.append('Independent QA ledger is stale: '+stage)
        if decisions[stage] and decisions[stage].get('jobs_digest')!=digests[stage]:errors.append('Adjudication ledger is stale: '+stage)
    s3=read_json(root/'audit'/'s3_receipt.json') if (root/'audit'/'s3_receipt.json').exists() else {'status':'NOT_RUN','optimizer_speedup_claim':False}
    complete=all(stage_complete.values()) and all(decisions.values()) and qa['status'] in ('CPU_SMOKE_QA_PASSED','INDEPENDENT_NUMERICAL_QA_PASSED') and qa.get('replay_enabled') and s3['status'] in ('S3_NO_GO','S3_EXECUTED') and not errors
    if not complete:state='INCOMPLETE_BLOCKED_EVIDENCE'
    elif cfg['profile']=='smoke':state='CPU_SMOKE_COMPLETE_NOT_SCIENTIFIC_VALIDATION'
    elif not decisions['s2']['coverage_qualified']:state='INCOMPLETE_BLOCKED_EVIDENCE'
    else:
        u=decisions['s2']['utility']['utility_gate_pass'];s=decisions['s2']['structure']['verdict']
        state='COMPLETE_MIXED' if u or s.startswith(('GENERIC','STRUCTURE_CONFIRMED')) else 'COMPLETE_NEGATIVE'
    rows=[flatten_utility(r) for r in records];tables={}
    tables['utility_all_states']=write_table(root,'utility_all_states',rows)
    inventory=[{k:j[k] for k in ('id','stage','kind','state','attempts')}|{'run_id':j['payload'].get('run',{}).get('run_id'),'result':j['result']} for j in jobs]
    tables['run_inventory']=write_table(root,'run_inventory',inventory)
    bins=[];blocks=[];probes=[];nulls=[];claims=[]
    for record in records:
        path=root/'measurements'/record['job_id']/'result.json';receipt=file_receipt(path,root);u=record['utility'];s=record.get('structure')
        claims.append({'claim_id':'measurement-'+record['job_id'][:16],'estimand':'best-scaled layerwise GGN regret',
                       'value':u.get('delta'),'evidence_grade':'SMOKE_ONLY' if cfg['profile']=='smoke' else u['status'],
                       'independent_seed':record['provenance']['seed'],'source_path':receipt['path'],'source_sha256':receipt['sha256'],
                       'checkpoint_sha256':record['provenance']['checkpoint_integrity_sha'],'protocol_sha256':lock['protocol_sha'],
                       'limitation':'One correlated checkpoint/damping measurement, not an independent population conclusion'})
        if not s:continue
        for kind,key in [('raw_inverse','raw_profile'),('interaction','correction_profile'),('raw_GGN','GGN_profile')]:
            p=s.get(key)
            if p and p.get('normalized_element_rms'):
                for k,(energy,ratio) in enumerate(zip(p['bin_energy'],p['normalized_element_rms'])):
                    bins.append({'job_id':record['job_id'],'kind':kind,'distance':k,'energy':energy,'normalized_element_rms':ratio,'status':s['status']})
        if s.get('energy_mean'):
            for i,row in enumerate(s['energy_mean']):
                for j,value in enumerate(row):blocks.append({'job_id':record['job_id'],'target':i,'source':j,'energy':value,'standard_error':s['energy_se'][i][j],'status':s['status']})
        if s.get('probe_artifact'):
            raw=read_json(root/s['probe_artifact']['path'])
            for phase,entries in raw.items():
                for entry in entries:probes.append({'job_id':record['job_id'],'phase':phase,**entry})
        if s.get('order_null'):nulls.append({'job_id':record['job_id'],**s['order_null']})
    for name,value in [('structure_all_bins',bins),('all_block_energies',blocks),('probe_results',probes),('null_results',nulls),('claim_ledger',claims)]:tables[name]=write_table(root,name,value)
    tables['numerical_eligibility']=write_table(root,'numerical_eligibility',[{'job_id':r['job_id'],'status':r['status'],'reason':r['utility'].get('reason'),'solver_delta_stability':r['utility'].get('delta_stability'),'structure_status':(r.get('structure') or {}).get('status')} for r in records])
    checkpoint_rows=[]
    for job in jobs:
        if job['kind']=='train' and job.get('result',{}).get('receipt'):
            tr=read_json(root/job['result']['receipt']['path'])
            checkpoint_rows.extend([{'run_id':tr['run_id'],**c} for c in tr.get('checkpoints',[])])
    tables['checkpoints']=write_table(root,'checkpoints',checkpoint_rows)
    figures=generate_figures(root,records)
    scope='CPU ENGINEERING SMOKE: no RTX 4070 Ti validation and no S1/S2 scientific claims.' if cfg['profile']=='smoke' else 'Prospective recorded study; conclusions are limited to tested architectures/tasks/parameterization.'
    header=f'# GENESIS v2 — {state}\n\n{scope}\n\nProtocol SHA: `{lock["protocol_sha"]}`\n\n'
    verdict=header+f'## Execution\n\nJobs: `{counts}`. Independent QA: **{qa["status"]}**. S3: **{s3["status"]}**.\n\n'
    verdict+='## Independent endpoints\n\n'
    for s,decision in decisions.items():
        if decision:verdict+=f'### {s.upper()}\n\nU: `{decision["verdict"]}`; S: `{decision["structure"]["verdict"]}`; M: `{decision["mechanism"]["verdict"]}`; P: `{decision["prediction"]["status"]}`.\n\n'
    verdict+='No universal plateau, gauge-only explanation or optimizer speedup is inferred from a heatmap, unit test, or local oracle. See claim ledger for artifact-level evidence.\n\n'
    if errors or qa.get('errors'):verdict+='## Blocking evidence issues\n\n'+ '\n'.join('- '+x for x in errors+qa.get('errors',[]))+'\n'
    atomic_bytes(root/'reports'/'SCIENTIFIC_VERDICT.md',verdict.encode())
    details=header
    for stage,a in decisions.items():
        if a:details+=f'## {stage.upper()} utility conditions\n\n'+_markdown_table(a['utility']['conditions'],['setting_id','independent_seed_n','status','holm_p','pass'])+'\n'
    atomic_bytes(root/'reports'/'S_M_U_P_RESULTS.md',details.encode())
    failed=[r for r in inventory if r['state'] not in ('COMPLETE',)]
    reports={
      'NUMERICAL_QA.md':header+'## Independent readback\n\n```json\n'+json.dumps({k:qa.get(k) for k in ('status','errors','independent_replays','reviewer_type')},indent=2)+'\n```\n',
      'NEGATIVE_RESULTS.md':header+'Every invalid record remains in the planned denominator. NUMERIC_UNRESOLVED is not a negative scientific observation.\n\n'+_markdown_table(failed,['id','stage','kind','state','result']),
      'STATISTICAL_ANALYSIS.md':header+'Training seed is the independent unit. Primary per-gamma endpoint is the median of checkpoint 1/2/3 within a seed. At least two damping tests use a partial-conjunction test, then Holm correction across settings. Source-stratified probe bootstrap is separate Monte Carlo uncertainty.\n\n```json\n'+json.dumps(cfg['statistics'],indent=2)+'\n```\n',
      'REPRODUCTION.md':header+'Install the exact environment in env-lock.json; use the frozen source/config/dataset checksums. Run `genesis --config <same yaml> --root <same root> verify --independent --all`, then `report`. Never unpickle unknown checkpoints. Resume from committed safetensors transactions. The experiment source hash must match protocol-lock.json.\n',
      'RESOURCE_ACCOUNTING.md':header+'Measured diagnostics wall seconds: '+str(sum(r['wall_seconds'] for r in records))+'\n\nMeasured diagnostic GGN matvecs: '+str(sum(r['total_GGN_matvecs'] for r in records))+'\n\n'+json.dumps(read_json(root/'resource_status.json') if (root/'resource_status.json').exists() else {'resource_receipt':'not available'},indent=2)+'\n\nPublic datasets, optimizer calibration and training costs are retained separately in their receipts; do not report the diagnostic total as total study GPU time.\n',
      'FIGURE_INDEX.md':header+'\n'.join(f"- `{r['path']}` — SHA256 `{r['sha256']}`" for r in figures)+'\n'
    }
    for name,text in reports.items():atomic_bytes(root/'reports'/name,text.encode())
    atomic_json(root/'reports'/'INDEPENDENT_VERIFIER_RECEIPT.json',qa)
    atomic_bytes(root/'reports'/'index.html',('<!doctype html><html lang="en"><meta charset="utf-8"><title>GENESIS evidence report</title><body><pre>'+html.escape(verdict+details)+'</pre></body></html>').encode())
    atomic_json(root/'tables'/'table_manifest.json',tables)
    result={'state':state,'profile':cfg['profile'],'source_of_truth':'protocol-lock.json + raw job artifacts + independent verifier',
            'counts':counts,'figures':figures,'tables':tables,'report':file_receipt(root/'reports'/'SCIENTIFIC_VERDICT.md',root),
            'scientific_complete':complete and cfg['profile']=='full' and state!='INCOMPLETE_BLOCKED_EVIDENCE'}
    set_state(root,state,scientific_complete=result['scientific_complete']);atomic_json(root/'reports'/'report_receipt.json',result)
    manifest=[]
    for path in sorted(root.rglob('*')):
        if path.is_file() and any(parent in path.parts for parent in ('reports','figures','tables')) and path.name!='manifest_sha256.txt':
            manifest.append(f'{sha256_file(path)}  {path.relative_to(root).as_posix()}')
    atomic_bytes(root/'manifest_sha256.txt',('\n'.join(manifest)+'\n').encode())
    return result
