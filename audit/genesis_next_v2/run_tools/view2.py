import json,numpy as np,collections
O=r'E:\GENESIS\runs\genesis_next_v2'
g=collections.Counter();iso=[];cov=[];drift=[]
for l in open(O+r'\STRUCTURE_MECHANISM_RESULTS.jsonl'):
    r=json.loads(l)
    for z in (r['gauge'] or []):
        g[z['status']]+=1;iso.append(abs(z['isotropic_delta_change']));cov.append(z['covariant_delta_error']);drift.append(z['actual_forward_relative_drift'])
print('gauge',dict(g),'iso |dDelta| median/max',np.median(iso),max(iso),'cov err max',max(cov),'fwd drift max',max(drift))
a=[];
for l in open(O+r'\NUMERICAL_ERROR_AUDIT.jsonl'):
    r=json.loads(l)
    if r['record']=='delta_attribution' and 'delta_reference_fp64' in r:a.append(r)
print(len(a))
f=lambda k:np.array([x[k] for x in a if x.get(k) is not None])
for k in ('input_quantization_effect','fp32_arithmetic_effect','v2_total_error'):
    v=f(k);print(k,len(v),'median|.|',np.median(abs(v)),'max|.|',abs(v).max())
big=[x for x in a if x.get('v2_total_error') is not None and abs(x['v2_total_error'])>1e-3];print('v2 err >1e-3',len(big))
un=[x for x in a if x['v2_recorded_status']!='NUMERIC_VALID'];print('v2 unresolved but FP64 valid',len(un), 'delta range',min(x['delta_reference_fp64'] for x in un),max(x['delta_reference_fp64'] for x in un))
for x in sorted(a,key=lambda x:-abs(x.get('v2_total_error') or 0))[:3]:print(x['setting_id'],x['gamma'],x['delta_reference_fp64'],x['v2_recorded_delta'],x['input_quantization_effect'],x['fp32_arithmetic_effect'])
neg=[];nm=[]
for l in open(O+r'\STRUCTURE_MECHANISM_RESULTS.jsonl'):
    r=json.loads(l);h=r['hessian_by_rank_tolerance'][1];nm.append(h['negative_mass_fraction']);neg.append(h['relative_H_G_fro'])
print('H-G fro median',np.median(neg),'neg mass median',np.median(nm),max(nm))
