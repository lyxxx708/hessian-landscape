"""GENESIS command line. Production is CUDA/E:-first, smoke is explicitly separate."""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import os
import sys
import time
import yaml
from genesis_gpu.study.design import default_config,load_config,expand_design
from genesis_gpu.runtime.atomic_io import atomic_json,read_json
from genesis_gpu.env.storage_guard import prepare_storage,configure_process_environment


def parser():
    p=argparse.ArgumentParser(prog='genesis',description=__doc__)
    p.add_argument('--config',default='configs/study_v2.yaml');p.add_argument('--root')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('doctor','prepare-data','import-local-images','g0','freeze','plan','run','resume','status','stop','pause','adjudicate','verify','report','pipeline','init-config'):
        s=sub.add_parser(name)
        s.add_argument('--config',default=argparse.SUPPRESS);s.add_argument('--root',default=argparse.SUPPRESS)
        if name=='init-config':s.add_argument('--profile',choices=['full','smoke'],default='full');s.add_argument('--output',required=True)
        if name in ('doctor','g0'):s.add_argument('--device');s.add_argument('--storage')
        if name in ('prepare-data','pipeline'):s.add_argument('--accept-licenses',action='store_true')
        if name=='import-local-images':
            s.add_argument('--mnist-raw',type=Path,required=True,help='Folder containing four canonical MNIST .gz files')
            s.add_argument('--cifar-batches',type=Path,required=True,help='cifar-10-batches-py folder')
            s.add_argument('--confirm-authorized-local-use',action='store_true',
                           help='Attest owner authorization for local research without redistribution')
        if name in ('g0','verify'):s.add_argument('--all',action='store_true')
        if name=='g0':s.add_argument('--save-reference',action='store_true')
        if name in ('plan','run','resume','adjudicate'):s.add_argument('--stage',default='s1')
        if name=='plan':s.add_argument('--dry-run',action='store_true')
        if name in ('run','resume'):
            s.add_argument('--resume',action='store_true');s.add_argument('--max-jobs',type=int)
            s.add_argument('--unlock-only-after-s1-adjudication',action='store_true')
            s.add_argument('--only-if-gate-pass',action='store_true')
        if name=='status':s.add_argument('--json',action='store_true')
        if name=='verify':s.add_argument('--independent',action='store_true');s.add_argument('--hash-only',action='store_true')
        if name=='report':s.add_argument('--format',default='md,html')
        if name=='freeze':s.add_argument('--analysis',help='Analysis settings are part of the one config; separate external overrides refused')
    return p


def doctor(cfg,root):
    import torch
    from genesis_gpu.env.reproducibility import environment_receipt
    from genesis_gpu.runtime.resources import nvidia_status
    env=environment_receipt(cfg['device']);errors=[]
    if cfg['profile']=='full' and not torch.cuda.is_available():errors.append('CUDA_REQUIRED: install compatible CUDA torch; no CPU fallback')
    if cfg['profile']=='full':
        if os.name!='nt':errors.append('Production profile expects Windows E: storage; CPU smoke is the portable QA route')
        if torch.cuda.is_available():
            gpu=nvidia_status(torch.device(cfg['device']).index or 0);env['nvidia_smi']=gpu
            if gpu.get('total_mib',0)<10_000:errors.append('Device VRAM does not match 12GB-class design')
    try:
        prepare_storage(root,production=cfg['profile']=='full',min_free_bytes=int(cfg['resources']['disk_reserve_gib']*1024**3))
        env['cache_paths']=configure_process_environment(Path(cfg['storage_root']),cfg['profile']=='full')
    except Exception as exc:errors.append(str(exc))
    receipt={'status':'ENV_READY' if not errors else 'ENV_BLOCKED','errors':errors,'environment':env,
             'cuda_qualification':'NOT_RUN','scientific_qualification':'NOT_RUN'}
    if Path(root).is_dir():atomic_json(Path(root)/'audit'/'doctor.json',receipt)
    return receipt


def execute(args,cfg,root):
    command=args.command
    if command=='doctor':return doctor(cfg,root)
    if command=='plan':
        from genesis_gpu.runtime.scheduler import plan_jobs
        if args.stage not in ('s1','s2'):raise ValueError('S3 is gated and planned by the benchmark runner after S2')
        runs=expand_design(cfg);lock={'protocol_sha':'DRY_RUN_NOT_FROZEN','runs':[r.to_dict() for r in runs]}
        jobs=plan_jobs(cfg,lock,args.stage)
        return {'stage':args.stage,'profile':cfg['profile'],'training_runs':sum(j['kind']=='train' for j in jobs),
                'measurement_jobs':sum(j['kind']=='measure' for j in jobs),'structure_jobs':sum(j['payload'].get('tier','B').startswith('C') for j in jobs),
                'status':'DRY_RUN_NO_SCIENCE','all_jobs':len(jobs)}
    if command in ('status','stop','pause'):
        if command in ('stop','pause'):
            if not (root/'protocol-lock.json').exists():raise RuntimeError('No identified study to control')
            atomic_json(root/'control.json',{'action':command,'time':time.time()});return {'action':command,'cooperative_only':True,'other_processes_killed':False}
        from genesis_gpu.runtime.scheduler import status
        return status(root)
    if command=='import-local-images':
        if (root/'protocol-lock.json').exists():
            raise RuntimeError('Study already frozen: create a new protocol/root instead of replacing inputs')
        if not args.confirm_authorized_local_use:
            raise RuntimeError('Explicit --confirm-authorized-local-use required; never assume licence from download')
    prepare_storage(root,production=cfg['profile']=='full',min_free_bytes=int(cfg['resources']['disk_reserve_gib']*1024**3))
    configure_process_environment(Path(cfg['storage_root']),cfg['profile']=='full')
    if command=='prepare-data':
        from genesis_gpu.datasets.registry import prepare_data
        return prepare_data(cfg,root,accept_licenses=args.accept_licenses)
    if command=='import-local-images':
        from genesis_gpu.datasets.offline_import import import_local_images
        return import_local_images(cfg,root,mnist_raw=args.mnist_raw,cifar_batches=args.cifar_batches,
                                   authorized_local_use=args.confirm_authorized_local_use,
                                   production=cfg['profile']=='full')
    if command=='g0':
        from genesis_gpu.audit.g0 import run_g0
        if (root/'protocol-lock.json').exists():raise RuntimeError('Already frozen: use verify, not overwrite G0 evidence')
        return run_g0(cfg,root)
    if command=='freeze':
        from genesis_gpu.study.freeze import freeze_protocol
        if args.analysis:raise ValueError('Analysis must be inside immutable config, not an ignored second file')
        lock=freeze_protocol(cfg,root);return {'status':'PROTOCOL_FROZEN','protocol_sha':lock['protocol_sha'],'run_count':len(lock['runs'])}
    if command in ('run','resume'):
        if args.stage=='s3':
            from genesis_gpu.training.benchmark import run_benchmark
            return run_benchmark(cfg,root)
        from genesis_gpu.runtime.scheduler import run_stage
        return run_stage(cfg,root,args.stage,max_jobs=args.max_jobs,resume=args.resume or command=='resume')
    if command=='adjudicate':
        from genesis_gpu.study.adjudication import adjudicate
        return {stage:adjudicate(cfg,root,stage) for stage in args.stage.split(',')}
    if command=='verify':
        from genesis_gpu.audit.verify import verify_study
        return verify_study(cfg,root,replay=not args.hash_only,all_records=args.all)
    if command=='report':
        from genesis_gpu.reporting.report import generate_report
        return generate_report(cfg,root)
    if command=='pipeline':
        from genesis_gpu.datasets.registry import prepare_data
        from genesis_gpu.audit.g0 import run_g0
        from genesis_gpu.study.freeze import freeze_protocol,verify_lock
        from genesis_gpu.runtime.scheduler import run_stage
        from genesis_gpu.study.adjudication import adjudicate
        from genesis_gpu.training.benchmark import run_benchmark
        from genesis_gpu.audit.verify import verify_study
        from genesis_gpu.reporting.report import generate_report
        receipt=doctor(cfg,root)
        if receipt['errors']:raise RuntimeError('Environment blocked: '+str(receipt['errors']))
        if not (root/'protocol-lock.json').exists():
            prepare_data(cfg,root,accept_licenses=args.accept_licenses);run_g0(cfg,root);freeze_protocol(cfg,root)
        else:verify_lock(cfg,root)
        for stage in ('s1','s2'):
            r=run_stage(cfg,root,stage,resume=True)
            if not r['execution_complete']:return {'status':'INTERRUPTED','stage':stage,'counts':r['counts']}
            adjudicate(cfg,root,stage)
        run_benchmark(cfg,root);verify_study(cfg,root,replay=True);return generate_report(cfg,root)
    raise ValueError('Unsupported command')


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=='init-config':
            output=Path(args.output)
            if output.exists():raise FileExistsError('Refuse to overwrite existing config')
            output.parent.mkdir(parents=True,exist_ok=True);output.write_text(yaml.safe_dump(default_config(args.profile),sort_keys=False),encoding='utf-8')
            print(json.dumps({'created':str(output),'profile':args.profile}));return 0
        cfg=load_config(Path(args.config))
        if args.root:cfg['root']=str(Path(args.root))
        if getattr(args,'device',None):cfg['device']=args.device
        if getattr(args,'storage',None):cfg['storage_root']=args.storage
        root=Path(cfg['root'])
        result=execute(args,cfg,root)
        # Keep the console small. All full receipts are on disk.
        if args.command in ('status','plan','doctor'):output=result
        else:output={k:v for k,v in result.items() if k in ('status','state','stage','profile','protocol_sha','counts','execution_complete','interrupted','processed','report','errors','run_count')}
        if not output:output={'command':args.command,'receipt_written':True}
        print(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False))
        status=result.get('status',result.get('state',''))
        return 2 if status in ('QA_FAILED','G0_FAILED','ENV_BLOCKED','INCOMPLETE_BLOCKED_EVIDENCE','INTERRUPTED') else 0
    except KeyboardInterrupt:
        print(json.dumps({'status':'INTERRUPTED','reason':'user interrupt; committed artifacts preserved'}),file=sys.stderr);return 130
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','error':type(exc).__name__,'reason':str(exc)},ensure_ascii=False),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
