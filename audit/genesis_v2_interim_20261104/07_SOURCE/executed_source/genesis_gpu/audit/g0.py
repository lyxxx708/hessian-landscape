"""Executable numerical and device G0. CPU smoke can never authorize full CUDA science."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import io
import gc
import time
import torch
import numpy as np
from genesis_gpu.contracts import LossSpec,object_sha
from genesis_gpu.models.registry import build_model
from genesis_gpu.study.design import default_config,expand_design,seed_for,setting_specs
from genesis_gpu.datasets.registry import load_bundle
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.audit.independent_reference import dense_reference,independent_ggn_vector
from genesis_gpu.solvers.cg import cg,block_solve
from genesis_gpu.science.utility import quadratic_utility
from genesis_gpu.env.reproducibility import configure_determinism,environment_receipt
from genesis_gpu.runtime.atomic_io import atomic_json,atomic_bytes,file_receipt


def _relative(a,b):return float((a-b).norm()/b.norm().clamp_min(1e-30))


def _run_g0(cfg,root):
    root=Path(root);(root/'audit').mkdir(parents=True,exist_ok=True)
    if cfg['profile']=='full' and (not cfg['device'].startswith('cuda') or not torch.cuda.is_available()):
        raise RuntimeError('CUDA_G0_REQUIRED: CPU result cannot qualify this protocol')
    configure_determinism();env=environment_receipt(cfg['device']);checks=[];refs=[];hardware=[]
    tinycfg=default_config('smoke')
    device=cfg['device']
    try:
        for run in [r for r in expand_design(tinycfg) if r.stage=='s1']:
            run=replace(run,seed=seed_for('G0_ONLY',run.setting_id),stage='g0')
            bundle=load_bundle(run,tinycfg,root)
            model=build_model(run.model,run.seed).to(device=device,dtype=torch.float64)
            x,y=bundle.batch('train',step=0,count=2,seed=run.seed,device=device,dtype=torch.float64)
            loss=LossSpec('mse' if run.model.family=='dln' else 'ce')
            op=FrozenOperator(model,x,y,loss,microbatch=1)
            ref=dense_reference(op,with_hessian=len(op.theta)<100,parameter_limit=4000)
            v=torch.linspace(-1,1,len(op.theta),device=device,dtype=torch.float64)
            err=_relative(op.raw_ggn(v),ref['G']@v)
            errg=_relative(op.gradient(),ref['gradient'])
            h=op.hvp(v);eps=1e-5
            # Independent HVP: finite differences of separate reverse-autograd scalar gradients.
            def reverse_gradient(theta):
                t=theta.detach().requires_grad_(True)
                return torch.autograd.grad(op.objective(t),t)[0].detach()
            fd=(reverse_gradient(op.theta+eps*v)-reverse_gradient(op.theta-eps*v))/(2*eps)
            herr=_relative(h,fd)
            sol=cg(lambda a:op.matvec(a,.1),v,rtol=1e-9,max_iter=500)
            q=ref['G']+.1*torch.eye(len(v),dtype=v.dtype,device=v.device)
            serr=_relative(sol.direction,torch.linalg.solve(q,v))
            block,br=block_solve(op,v,.1,rtol=1e-9,max_iter=500)
            blockerr=0.
            for ids in op.layout.group_indices(device=v.device):
                blockerr=max(blockerr,_relative(block[ids],torch.linalg.solve(q[ids][:,ids],v[ids])))
            ok=err<1e-8 and errg<1e-8 and herr<5e-5 and serr<1e-7 and blockerr<1e-7 and sol.converged and all(r.converged for r in br)
            checks.append({'family':run.model.family,'GGNv_relative':err,'gradient_relative':errg,'HVP_fd_relative':herr,
                           'solve_forward_relative':serr,'block_forward_relative':blockerr,'passed':ok,'device':device})
            buffer=io.BytesIO();np.savez_compressed(buffer,J=ref['J'].cpu().numpy(),G=ref['G'].cpu().numpy(),gradient=ref['gradient'].cpu().numpy(),
                                                  probe=v.cpu().numpy(),ggn_probe=op.raw_ggn(v).cpu().numpy())
            path=root/'audit'/f'g0_{run.model.family}_reference.npz';atomic_bytes(path,buffer.getvalue());refs.append(file_receipt(path,root))
            del op,model,ref;gc.collect()
        Q=torch.tensor([[1.,.9],[.9,1.]],dtype=torch.float64,device=device)
        values=[]
        for g in [torch.ones(2,dtype=Q.dtype,device=device),torch.tensor([1.,0.],dtype=Q.dtype,device=device)]:
            values.append(quadratic_utility(g,-torch.linalg.solve(Q,g),-g,-Q@g)['eta'])
        checks.append({'case':'two_gradient_spd_counterexample','values':values,'passed':abs(values[0]-1)<1e-10 and abs(values[1]-.19)<1e-10})
        # Independent dense ground truth for stochastic inverse-block estimation.
        # Replicates are Monte Carlo calibration, never independent training seeds.
        from genesis_gpu.sketches.block_probe import estimate_blocks
        from genesis_gpu.science.structure import exact_block_energies
        generator=torch.Generator(device=device);generator.manual_seed(19031)
        B=torch.randn((6,6),device=device,dtype=torch.float64,generator=generator)
        G=B.T@B/6;lam=.2;Q=G+lam*torch.eye(6,device=device,dtype=G.dtype)
        R=torch.linalg.solve(Q,torch.eye(6,device=device,dtype=G.dtype))
        ids=[torch.arange(0,2,device=device),torch.arange(2,4,device=device),torch.arange(4,6,device=device)]
        exact=np.asarray(exact_block_energies(R,ids));estimates=[];se_values=[];coverages=[]
        for seed in range(8):
            sketch=estimate_blocks(lambda z:cg(lambda v:Q@v,z,rtol=1e-11,max_iter=100),lambda v:G@v,ids,lam,
                      dtype=G.dtype,device=device,seed=1087+seed,schedule=(16,32),relative_halfwidth=.2,bootstrap=80)
            estimates.append(sketch['energy_mean']);se_values.append(sketch['energy_se'])
            observed=np.array(sketch['energy_mean']);se=np.array(sketch['energy_se'])
            coverages.append(float(np.mean(np.abs(observed-exact)<=2*se+1e-10)))
        estimates=np.asarray(estimates);se_values=np.asarray(se_values)
        ensemble_se=np.sqrt(np.square(se_values).sum(0))/len(estimates)
        discrepancy=np.abs(estimates.mean(0)-exact)
        checks.append({'case':'block_estimator_ensemble','replicates':len(estimates),'exact_reference':True,
                       'max_standardized_mean_error':float(np.max(discrepancy/(ensemble_se+1e-10))),
                       'empirical_two_se_coverage':float(np.mean(coverages)),
                       'passed':bool(np.all(discrepancy<=6*ensemble_se+1e-10)),
                       'interpretation':'small fixed-seed numerical calibration; not a theorem of 95% interval coverage'})
        buf=io.BytesIO();np.savez_compressed(buf,exact=exact,replicates=estimates,standard_errors=se_values)
        refpath=root/'audit'/'g0_block_estimator_reference.npz';atomic_bytes(refpath,buf.getvalue());refs.append(file_receipt(refpath,root))
        if cfg['profile']=='full':
            # Cost preflight is excluded from inference, and covers each largest model family.
            specs=setting_specs();chosen={}
            for sid,m,t,data in specs:
                if m.family not in chosen or m.depth*m.width>chosen[m.family][1].depth*chosen[m.family][1].width:chosen[m.family]=(sid,m,t,data)
            from genesis_gpu.contracts import RunSpec
            for family,(sid,m,t,data) in chosen.items():
                seed=seed_for('HARDWARE_G0_ONLY',sid);run=RunSpec('g0-'+sid,sid,'g0',seed,0,m,t,data)
                bundle=load_bundle(run,cfg,root);model=build_model(m,seed).to(device)
                torch.cuda.reset_peak_memory_stats(device)
                loss=LossSpec('mse' if family=='dln' else 'ce');opt=torch.optim.AdamW(model.parameters(),lr=t.learning_rate)
                torch.cuda.synchronize(device);start=time.perf_counter()
                tx,ty=bundle.batch('train',step=0,count=t.effective_batch,seed=seed,device=device)
                total_den=int((ty!=loss.ignore_index).sum()) if loss.kind=='ce' else ty.numel()
                for offset in range(0,len(tx),t.microbatch):
                    px=model(tx[offset:offset+t.microbatch]);yy=ty[offset:offset+t.microbatch]
                    loss.value(px,yy,denominator=total_den).backward()
                opt.step();opt.zero_grad(set_to_none=True)
                from genesis_gpu.training.checkpoint import save_state
                statepath=root/'audit'/'preflight_checkpoints'/family
                if statepath.exists():
                    import shutil
                    shutil.rmtree(statepath)  # G0-only transient checkpoint, never scientific evidence.
                saved=save_state(statepath,{'model':model.state_dict(),'optimizer':opt.state_dict()}, {'stage':'G0_EXCLUDED','family':family})
                measured_bytes=sum(p.stat().st_size for p in statepath.rglob('*') if p.is_file())
                x,y=bundle.batch('train',step=0,count=cfg['curvature_batch'],seed=seed,device=device)
                op=FrozenOperator(model,x,y,loss,microbatch=min(cfg['curvature_microbatch'],len(x)))
                v=torch.randn_like(op.theta);a=op.raw_ggn(v);b=independent_ggn_vector(op,v)
                error=_relative(a,b);torch.cuda.synchronize(device)
                peak=torch.cuda.max_memory_allocated(device)
                record={'family':family,'setting':sid,'seed_namespace':'HARDWARE_G0_ONLY','seconds':time.perf_counter()-start,
                        'peak_allocated':peak,'peak_reserved':torch.cuda.max_memory_reserved(device),'parameters':len(v),
                        'GGNv_independent_relative':error,'passed':error<2e-3 and peak<cfg['resources']['vram_target_gib']*1024**3,
                        'sample_checkpoint_measured_bytes':measured_bytes,'effective_batch':t.effective_batch,'curvature_batch':len(x),'warning':'time/VRAM preflight, not S1 evidence'}
                hardware.append(record)
                del model,op,opt;gc.collect();torch.cuda.empty_cache()
        disk_forecast=None
        if cfg['profile']=='full':
            from collections import Counter
            from genesis_gpu.env.storage_guard import ensure_space
            counts=Counter(r.model.family for r in expand_design(cfg))
            checkpoint_forecast=sum(h['sample_checkpoint_measured_bytes']*counts[h['family']]*9 for h in hardware)
            # Scalar-probe JSON, measurements, figures and caches; no P-dimensional probe vectors by default.
            projected=int(checkpoint_forecast*1.5)
            free=ensure_space(root,int(cfg['resources']['disk_reserve_gib']*1024**3),projected)
            disk_forecast={'projected_checkpoint_and_diagnostic_bytes':projected,'current_free_bytes':free,
                           'basis':'measured largest-family complete model+optimizer checkpoint x9 copies/trajectory x1.5 diagnostic margin',
                           'scope':'S1/S2; S3 costs recorded separately and disk guard remains active'}
            atomic_json(root/'audit'/'disk_forecast.json',disk_forecast)
        passed=all(c['passed'] for c in checks) and (cfg['profile']!='full' or len(hardware)==4 and all(h['passed'] for h in hardware))
        status=('CUDA_G0_NUMERIC_VALID' if cfg['profile']=='full' else 'CPU_SMOKE_G0_VALID') if passed else 'G0_FAILED'
        receipt={'status':status,'config_sha':object_sha(cfg),'source_sha':env['source']['sha256'],'environment':env,
                 'checks':checks,'hardware_preflight':hardware,'disk_forecast':disk_forecast,'reference_artifacts':refs,
                 'qualifies_production':cfg['profile']=='full' and passed,'scientific_experiments_executed':False}
        atomic_json(root/'audit'/'g0_receipt.json',receipt);atomic_json(root/'env-lock.json',env)
        if not passed:raise RuntimeError('G0 failed: see audit/g0_receipt.json; no science is authorized')
        return receipt
    except Exception as exc:
        previous=root/'audit'/'g0_receipt.json'
        if previous.exists():
            from genesis_gpu.runtime.atomic_io import sha256_file
            atomic_bytes(root/'audit'/'history'/('g0_'+sha256_file(previous)+'.json'),previous.read_bytes())
        atomic_json(previous,{'status':'G0_FAILED','config_sha':object_sha(cfg),'source_sha':env['source']['sha256'],
                             'checks':checks,'hardware_preflight':hardware,'error':repr(exc),'qualifies_production':False})
        raise


def run_g0(cfg,root):
    from genesis_gpu.runtime.resources import DeviceLock,StudyLock
    with DeviceLock(cfg['storage_root'],cfg['device'],cfg['device'].startswith('cuda')),StudyLock(root):
        return _run_g0(cfg,root)
