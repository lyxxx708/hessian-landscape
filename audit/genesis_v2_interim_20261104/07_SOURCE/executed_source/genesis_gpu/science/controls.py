import numpy as np
from genesis_gpu.science.structure import profile


def order_null(energy,sizes,permutations=128,seed=55):
    E=np.asarray(energy);sizes=np.asarray(sizes);rng=np.random.default_rng(seed)
    observed=profile(E,sizes)
    if observed['tail_cv'] is None:
        return {'status':'SHORT_DEPTH','p_flatness':None,'permutations':permutations}
    null=[]
    for _ in range(permutations):
        p=rng.permutation(len(sizes))
        value=profile(E[np.ix_(p,p)],sizes[p])['tail_cv']
        null.append(value)
    p=(1+sum(v<=observed['tail_cv']+1e-12 for v in null))/(1+len(null))
    return {'status':'COMPUTED','observed_cv':observed['tail_cv'],'null_cv':null,'p_flatness':p,
            'interpretation':'randomizes layer-distance labels only; simultaneous permutation cannot establish changed optimization utility'}


def spectral_subspace_null(matrix,rank,seed=2,repeats=32):
    M=np.asarray(matrix);n=len(M)
    if not 0<rank<n:raise ValueError('Nontrivial matched rank required')
    U,s,_=np.linalg.svd(M,full_matrices=False)
    top=U[:,:rank]
    denom=np.linalg.norm(M)
    actual=np.linalg.norm(M-top@(top.T@M))/denom if denom else 0.
    rng=np.random.default_rng(seed);values=[]
    for _ in range(repeats):
        Q,_=np.linalg.qr(rng.standard_normal((n,rank)))
        values.append(float(np.linalg.norm(M-Q@(Q.T@M))/denom) if denom else 0.)
    return {'rank':rank,'retained_residual_fraction':float(actual),'random_rank_matched_residuals':values,
            'not_masked_energy_additivity':True}
