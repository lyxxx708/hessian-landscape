import copy
import numpy as np
import torch
from genesis_gpu.audit.independent_reference import dense_reference
from genesis_gpu.curvature.operators import FrozenOperator
from genesis_gpu.science.structure import exact_block_energies,profile
from genesis_gpu.science.controls import spectral_subspace_null


def dense_mechanism(op,dampings,parameter_limit=2048):
    reference=dense_reference(op,with_hessian=True,parameter_limit=parameter_limit)
    G,H,g=reference['G'],reference['H'],reference['gradient']
    eig,V=torch.linalg.eigh((G+G.T)/2)
    tol=100*torch.finfo(eig.dtype).eps*max(1.,float(eig.abs().max()))*len(eig)
    active=eig>tol;null=V[:,~active]
    null_g=null@(null.T@g)
    eH,U=torch.linalg.eigh((H+H.T)/2)
    tolH=100*torch.finfo(eig.dtype).eps*max(1.,float(eH.abs().max()))*len(eH)
    rows=[];ids=op.layout.group_indices('coarse',device=g.device)
    for lam in dampings:
        R=(V/(eig+lam))@V.T
        p0=null@null.T
        horizontal=R-p0/lam
        shifted=eH+lam;pole=float(shifted.abs().min());spd=bool(shifted.min()>tolH)
        row={'damping':lam,'GGN_null_component_fro':float((p0/lam).norm()),'GGN_horizontal_component_fro':float(horizontal.norm()),
             'H_min_eigenvalue':float(eH.min()),'H_shifted_spd':spd,'pole_distance':pole,'H_condition_2':float(shifted.abs().max()/shifted.abs().min()) if pole>0 else None}
        if pole>1e-10*max(1.,float(shifted.abs().max())):
            RH=(U/shifted)@U.T
            row['H_inverse_profile']=profile(exact_block_energies(RH,ids),op.layout.group_sizes())
        else:row['H_inverse_status']='NEAR_POLE_NOT_ELIGIBLE'
        row['GGN_inverse_profile']=profile(exact_block_energies(R,ids),op.layout.group_sizes())
        rows.append(row)
    rank=int(active.sum());n=len(g)
    return {'status':'DENSE_REFERENCE','rank_G':rank,'nullity_G':n-rank,
            'null_gradient_relative':float(null_g.norm()/g.norm().clamp_min(1e-30)),
            'H_negative_count_tolerance':int((eH<-tolH).sum()),'H_near_zero_count':int((eH.abs()<=tolH).sum()),
            'H_sign_tolerance':tolH,'relative_H_G_gap':float((H-G).norm()/H.norm().clamp_min(1e-30)),
            'finite_lambda_horizontal_nonzero':any(r['GGN_horizontal_component_fro']>1e-12 for r in rows),
            'damping_sweep':rows,
            'residual_rank_control':spectral_subspace_null((H-G).cpu().numpy(),min(max(1,rank),n-1)) if n>1 else None}


def dln_gauge_controls(op,scales=(.5,2.,10.)):
    if getattr(getattr(op.model,'genesis_spec',None),'family',None)!='dln':
        return []
    before=op.prediction;rows=[]
    probe=torch.linspace(-1.,1.,len(op.theta),device=op.theta.device,dtype=op.theta.dtype)
    gv=op.raw_ggn(probe)
    base_ref=dense_reference(op,with_hessian=False,parameter_limit=128) if len(op.theta)<=128 else None
    lam=.01*max(float(torch.linalg.eigvalsh(base_ref['G']).max()) if base_ref is not None else float(gv.norm()/probe.norm()),1e-12)
    if base_ref is not None:
        identity=torch.eye(len(probe),device=probe.device,dtype=probe.dtype)
        before_R=torch.linalg.solve(base_ref['G']+lam*identity,identity)
        before_profile=profile(exact_block_energies(before_R,op.layout.group_indices(device=probe.device)),op.layout.group_sizes())
    for scale in scales:
        if scale<=0:raise ValueError('Positive invertible gauge scaling required')
        model=copy.deepcopy(op.model)
        with torch.no_grad():
            model.layers[0].weight.mul_(scale);model.layers[1].weight.div_(scale)
        changed=FrozenOperator(model,op.inputs,op.targets,op.loss,microbatch=op.microbatch)
        drift=float((changed.prediction-before).norm()/before.norm().clamp_min(1e-30))
        control={'GGNv_relative_change':float((changed.raw_ggn(probe)-gv).norm()/gv.norm().clamp_min(1e-30)),
                 'same_parameter_coordinate_probe':True,'same_damping':True,'damping':lam}
        if base_ref is not None:
            after_ref=dense_reference(changed,with_hessian=False,parameter_limit=128)
            after_R=torch.linalg.solve(after_ref['G']+lam*identity,identity)
            control.update(before_inverse_profile=before_profile,after_inverse_profile=profile(exact_block_energies(after_R,changed.layout.group_indices(device=probe.device)),changed.layout.group_sizes()))
        else:control['inverse_profile_status']='EXCLUDED_DENSE_COST; directional coordinate sensitivity only'
        rows.append({'curvature_control':control,'scale':scale,'relative_output_drift':drift,
                     'parameter_norm_ratio':float(changed.theta.norm()/op.theta.norm()),
                     'gradient_norm_ratio':float(changed.gradient().norm()/op.gradient().norm().clamp_min(1e-30)),
                     'warning':'Euclidean lambda I does not transform covariantly under nonorthogonal gauge scaling'})
    return rows
