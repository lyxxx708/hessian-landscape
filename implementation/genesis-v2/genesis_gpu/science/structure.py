import math
import numpy as np


def profile(energy,sizes):
    E=np.asarray(energy,dtype=float);sizes=np.asarray(sizes,dtype=int)
    L=len(sizes)
    if E.shape!=(L,L) or np.any(E<0) or not np.isfinite(E).all() or np.any(sizes<=0):
        raise ValueError('Invalid squared block energy or block sizes')
    bins=np.zeros(L);counts=np.zeros(L);elements=np.zeros(L)
    for i in range(L):
        for j in range(L):
            k=abs(i-j);bins[k]+=E[i,j];counts[k]+=1;elements[k]+=sizes[i]*sizes[j]
    total=float(bins.sum())
    if total==0 or bins[0]==0:
        return {'status':'ZERO_OR_DIAGONAL_FREE_ENERGY','bin_energy':bins.tolist(),'normalized_element_rms':None,
                'offdiag_mass':None,'tail_status':'NOT_ELIGIBLE','tail_cv':None,'tail_amplitude':None}
    rms=np.sqrt(bins/elements);c=rms/rms[0]
    result={'layers':L,'status':'VALID','bin_energy':bins.tolist(),'pair_counts':counts.tolist(),'element_counts':elements.tolist(),
            'normalized_element_rms':c.tolist(),'unnormalized_element_rms':rms.tolist(),
            'offdiag_mass':float(bins[1:].sum()/total),'mass_by_distance':(bins/total).tolist(),
            'tail_status':'SHORT_DEPTH','tail_cv':None,'tail_amplitude':None,
            'transpose_relative_error':float(np.linalg.norm(E-E.T)/max(np.linalg.norm(E),1e-300))}
    if L>=8:
        idx=np.arange(math.ceil(L/2),L-1);weights=counts[idx]/counts[idx].sum()
        mean=float(weights@c[idx]);var=float(weights@((c[idx]-mean)**2))
        result.update(tail_status='ELIGIBLE' if mean>0 else 'ZERO_SIGNAL',tail_amplitude=mean,
                      tail_cv=math.sqrt(var)/mean if mean>0 else None,tail_bins=idx.tolist())
    return result


def exact_block_energies(matrix,indices):
    return np.array([[float((matrix[i][:,j].square()).sum()) for j in indices] for i in indices])
