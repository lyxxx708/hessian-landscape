"""Source-block Rademacher energies; adaptive pilots + independent final probes.

No probe solution vectors are retained by default. Ratios are not claimed unbiased.
"""
import hashlib
import numpy as np
import torch
from genesis_gpu.science.structure import profile


def probe_seed(seed,phase,source,k):
    return int.from_bytes(hashlib.sha256(f'{seed}|{phase}|{source}|{k}'.encode()).digest()[:8],'big')%(2**63-1)


def _bootstrap(raw,sizes,replicates,seed):
    # raw[source,probe,target]. Resample within source, never call probes training replicates.
    rng=np.random.default_rng(seed);L,n,_=raw.shape
    cs=[];masses=[];energies=[]
    for _ in range(replicates):
        E=np.stack([raw[j,rng.integers(0,n,n)].mean(0) for j in range(L)],axis=1)
        p=profile(E,sizes)
        if p['normalized_element_rms'] is not None:
            cs.append(p['normalized_element_rms']);masses.append(p['offdiag_mass']);energies.append(p['bin_energy'])
    if not cs:return {'profile_ci':None,'mass_ci':None,'bin_ci':None}
    return {'profile_ci':np.quantile(cs,[.025,.975],axis=0).T.tolist(),
            'mass_ci':np.quantile(masses,[.025,.975]).tolist(),
            'bin_ci':np.quantile(energies,[.025,.975],axis=0).T.tolist()}


def estimate_blocks(solve,raw_ggn,indices,damping,*,dtype,device,seed=77,schedule=(16,32,64,128,256),
                    relative_halfwidth=.2,bootstrap=1000,independent_final=True,callback=None):
    if damping<=0 or len(schedule)==0 or min(schedule)<2 or list(schedule)!=sorted(set(schedule)):
        raise ValueError('Invalid probe schedule/damping')
    indices=[i.to(device) for i in indices];sizes=[len(i) for i in indices];P=sum(sizes);L=len(sizes)
    all_ids=torch.cat(indices)
    if len(torch.unique(all_ids))!=P or int(all_ids.max())!=P-1:
        raise ValueError('Probe groups must partition the whole operator')
    pilot_raw=[[] for _ in range(L)];pilot_cor=[[] for _ in range(L)];pilot_records=[]
    def sample(phase,start,end,raw,cor,records):
        for source,idx in enumerate(indices):
            for k in range(start,end):
                if callback:callback()
                s=probe_seed(seed,phase,source,k);rng=torch.Generator(device=device);rng.manual_seed(s)
                z=torch.zeros(P,device=device,dtype=dtype)
                z[idx]=(torch.randint(0,2,(len(idx),),generator=rng,device=device)*2-1).to(dtype)
                result=solve(z)
                if not result.converged:
                    return False,result.status
                x=result.direction
                # C z = -G R z/lambda is stable even when x - z/lambda suffers cancellation.
                correction=-raw_ggn(x)/damping
                raw_residual=raw_ggn(x)+damping*x-z
                gz=raw_ggn(z)
                c_residual=raw_ggn(correction)+damping*correction+gz/damping
                error_bound=float(raw_residual.norm())/damping
                c_error_bound=float(c_residual.norm())/damping
                e=[float(x[ii].square().sum()) for ii in indices]
                ce=[float(correction[ii].square().sum()) for ii in indices]
                bounds=[2*np.sqrt(v)*error_bound+error_bound**2 for v in e]
                cbounds=[2*np.sqrt(v)*c_error_bound+c_error_bound**2 for v in ce]
                raw[source].append(e);cor[source].append(ce)
                records.append({'source':source,'index':k,'phase':phase,'seed':s,'energy':e,'correction_energy':ce,'GGN_energy':[float(gz[ii].square().sum()) for ii in indices],
                                'energy_error_bound':bounds,'correction_energy_error_bound':cbounds,
                                'true_residual':result.true_residual,'iterations':result.iterations,'wall_time':result.wall_time,
                                'forward_error_bound_spd':error_bound,'correction_forward_error_bound_spd':c_error_bound})
        return True,None
    previous=0;chosen=schedule[-1];pilot_history=[]
    for n in schedule:
        good,reason=sample('pilot',previous,n,pilot_raw,pilot_cor,pilot_records)
        if not good:
            return {'status':'NUMERIC_UNRESOLVED','reason':'PROBE_SOLVE_'+reason,'pilot_records':pilot_records,'probe_records':[]}
        raw=np.array(pilot_raw);E=raw.mean(1).T
        p=profile(E,sizes);ci=_bootstrap(raw,sizes,min(bootstrap,200),seed+n)
        widths=np.diff(np.array(ci['profile_ci']),axis=1).ravel()/2
        c=np.array(p['normalized_element_rms']);valid=c>1e-12
        rel=float(np.max(widths[valid]/c[valid])) if valid.any() else float('inf')
        pilot_history.append({'n':n,'max_relative_halfwidth':rel})
        previous=n
        if rel<=relative_halfwidth:chosen=n;break
    if independent_final:
        raw=[[] for _ in range(L)];cor=[[] for _ in range(L)];records=[]
        good,reason=sample('final',0,chosen,raw,cor,records)
        if not good:return {'status':'NUMERIC_UNRESOLVED','reason':'FINAL_PROBE_'+reason,'pilot_records':pilot_records,'probe_records':records}
    else:
        raw,cor,records=pilot_raw,pilot_cor,pilot_records
    raw=np.array(raw);cor=np.array(cor);E=raw.mean(1).T;CE=cor.mean(1).T
    graw=np.array([[r['GGN_energy'] for r in records if r['source']==j] for j in range(L)])
    GE=graw.mean(1).T;gp=profile(GE,sizes)
    p=profile(E,sizes);cp=profile(CE,sizes)
    ci=_bootstrap(raw,sizes,bootstrap,seed+999);cci=_bootstrap(cor,sizes,bootstrap,seed+1001)
    widths=np.diff(np.array(ci['profile_ci']),axis=1).ravel()/2;c=np.array(p['normalized_element_rms'])
    relative=np.divide(widths,c,out=np.zeros_like(widths),where=c>1e-12)
    bounds=np.zeros_like(E);cbounds=np.zeros_like(E)
    for source in range(L):
        source_records=[r for r in records if r['source']==source]
        bounds[:,source]=np.mean([r['energy_error_bound'] for r in source_records],axis=0)
        cbounds[:,source]=np.mean([r['correction_energy_error_bound'] for r in source_records],axis=0)
    bin_bounds=[];correction_bin_bounds=[]
    for k in range(L):
        pairs=[(i,j) for i in range(L) for j in range(L) if abs(i-j)==k]
        bin_bounds.append(float(sum(bounds[i,j] for i,j in pairs)))
        correction_bin_bounds.append(float(sum(cbounds[i,j] for i,j in pairs)))
    energies=np.array(p['bin_energy']);bias_ok=bool(np.all(np.array(bin_bounds)<=.1*energies+1e-24))
    correction_bias_ok=bool(np.all(np.array(correction_bin_bounds)<=.1*np.array(cp['bin_energy'])+1e-24))
    status='NUMERIC_VALID' if max(relative)<=relative_halfwidth and bias_ok else 'UNCERTAIN'
    return {'status':status,'energy_mean':E.tolist(),'energy_se':(raw.std(1,ddof=1).T/np.sqrt(chosen)).tolist(),
            'GGN_energy_mean':GE.tolist(),'GGN_profile':gp,'GGN_uncertainty':_bootstrap(graw,sizes,bootstrap,seed+1003),
            'correction_energy_mean':CE.tolist(),'profile':p,'correction_profile':cp,'uncertainty':ci,'correction_uncertainty':cci,
            'probe_records':records,'pilot_records':pilot_records,'pilot_history':pilot_history,'probes_per_source':chosen,
            'independent_final':independent_final,'max_profile_relative_halfwidth':float(max(relative)),
            'solver_bias_qualified':bias_ok,'per_distance_energy_error_bound':bin_bounds,
            'correction_solver_bias_qualified':correction_bias_ok,'correction_per_distance_error_bound':correction_bin_bounds,'uncertainty_method':'source-stratified bootstrap on disjoint fixed-size final probes; finite-sample approximate',
            'ratio_bias_warning':'individual energies unbiased for exact solves; normalized RMS and mass ratios need not be unbiased'}
