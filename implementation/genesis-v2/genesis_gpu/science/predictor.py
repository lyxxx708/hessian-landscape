"""Small transparent S1-only ridge predictor. JSON coefficients, no pickle.

All features are cheap diagnostics or measured short-CG quantities. Neither full
GN gain, eta/delta, oracle full direction, nor S2 statistics enter features.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.model_selection import GroupKFold
from genesis_gpu.contracts import object_sha

FEATURES=('log_gamma','log_gradient','layer_scale_cv','log_condition_proxy','short_gain_per_gradient_sq','cheap_rho','matched_gain_per_gradient_sq','block_energy_proxy')
BASELINES={'damping':[0],'gradient':[1],'scales':[2],'condition':[3],'short_cg':[4],'matched_cg':[6],'block_energy':[7],'combined_cheap_without_rho':[0,1,2,3,4,6,7]}


def features(record):
    u=record['utility'];rho=u.get('cheap_rho');g=u.get('gradient_norm')
    if rho is None or g is None or not math.isfinite(rho) or g<=1e-12:return None
    gamma=record['gamma'];scale=record['spectral_scale']['value'];lam=record['lambda_absolute']
    vals=[math.log10(gamma),math.log10(g),u.get('layer_scale_cv',0.),math.log10(1+scale/lam),
          u.get('short_cg_quadratic_gain',0.)/(g*g),rho,
          u.get('matched_cg_quadratic_gain',0.)/(g*g),(u.get('block_energy_proxy') or {}).get('offdiag_fraction_proxy',0.)]
    return vals if all(v is not None and math.isfinite(v) for v in vals) else None


def dataset(records):
    rows=[]
    for r in records:
        p=r['provenance']
        if r['schema']!='coarse' or p['checkpoint_index']==0 or r['utility'].get('status')!='NUMERIC_VALID':continue
        f=features(r);y=r['utility'].get('delta')
        if f is not None and y is not None:rows.append((f,y,str(p['seed']),p['setting_id'],r['job_id']))
    if not rows:return np.empty((0,len(FEATURES))),np.empty(0),np.empty(0,dtype=str),[]
    return np.asarray([r[0] for r in rows]),np.asarray([r[1] for r in rows]),np.asarray([r[2] for r in rows]),[{'setting_id':r[3],'job_id':r[4]} for r in rows]


def _fit(X,y,alpha):
    mean=X.mean(0);std=X.std(0);std[std<1e-12]=1.
    Z=(X-mean)/std;bias=float(y.mean());coef=np.linalg.solve(Z.T@Z+alpha*np.eye(X.shape[1]),Z.T@(y-bias))
    return {'mean':mean.tolist(),'std':std.tolist(),'coef':coef.tolist(),'bias':bias,'alpha':alpha}


def predict(model,X):
    X=np.asarray(X);return np.clip(((X-np.array(model['mean']))/np.array(model['std']))@np.array(model['coef'])+model['bias'],0,1)


def fit_frozen_predictor(records,protocol_sha):
    if any(r['provenance']['stage']!='s1' for r in records):raise ValueError('S2 leakage: fitting accepts S1 ONLY')
    X,y,groups,_=dataset(records);n=len(np.unique(groups))
    result={'protocol_sha':protocol_sha,'feature_names':list(FEATURES),'training_seed_ids':sorted(set(groups.tolist())),
            'training_jobs_sha':object_sha(sorted(r['job_id'] for r in records)), 'independent_seed_n':n,'training_rows':len(y),'models':{}}
    if n<3:
        result.update(status='INSUFFICIENT_S1_GROUPS');return result
    indices={'candidate':list(range(len(FEATURES))),**BASELINES}
    for name,cols in indices.items():
        scores=[]
        for alpha in (.001,.1,1.,10.,100.):
            errors=[]
            for train,test in GroupKFold(n_splits=min(5,n)).split(X,y,groups):
                model=_fit(X[train][:,cols],y[train],alpha);pred=predict(model,X[test][:,cols])
                for group in np.unique(groups[test]):errors.append(float(np.mean(np.abs(y[test][groups[test]==group]-pred[groups[test]==group]))))
            scores.append((float(np.mean(errors)),alpha))
        error,alpha=min(scores)
        result['models'][name]={'columns':cols,'cv_group_mae':error,**_fit(X[:,cols],y,alpha)}
    result['status']='FROZEN_S1_ONLY';return result


def evaluate_predictor(model,records,cfg):
    if any(r['provenance']['stage']!='s2' for r in records):raise ValueError('Confirmation evaluation accepts S2 ONLY')
    X,y,groups,meta=dataset(records)
    if set(groups)&set(model['training_seed_ids']):raise ValueError('S1/S2 seed leakage detected')
    if model['status']!='FROZEN_S1_ONLY' or len(y)<4:
        return {'status':'NOT_EVALUABLE','prediction_gate_pass':False,'reason':'INSUFFICIENT_TRAIN_OR_CONFIRMATION','predictions':[]}
    n=len(set(groups));predictions={name:predict(m,X[:,m['columns']]) for name,m in model['models'].items()}
    labels=y>cfg['statistics']['delta_median']
    weights=np.array([1/sum(groups==g) for g in groups]);scores={}
    positive_seeds={g for g in set(groups) if labels[groups==g].any()};negative_seeds={g for g in set(groups) if (~labels[groups==g]).any()}
    classification_ok=len(positive_seeds)>=5 and len(negative_seeds)>=5 and len(np.unique(labels))==2
    for name,pred in predictions.items():
        mae=float(np.average(np.abs(pred-y),weights=weights))
        rho=float(spearmanr(y,pred).statistic) if np.std(y)>0 and np.std(pred)>0 else None
        scores[name]={'MAE':mae,'Spearman':rho if rho is not None and math.isfinite(rho) else None,
                      'AUROC':float(roc_auc_score(labels,pred,sample_weight=weights)) if classification_ok else None,
                      'PR_AUC':float(average_precision_score(labels,pred,sample_weight=weights)) if classification_ok else None}
    candidate=scores['candidate'];others=[s for name,s in scores.items() if name!='candidate'];s=cfg['statistics']
    # Bootstrap the paired MAE improvement at the independent cluster level.
    bestname=min((k for k in scores if k!='candidate'),key=lambda k:scores[k]['MAE'])
    gains=np.array([np.mean(np.abs(predictions[bestname][groups==g]-y[groups==g]))-
                    np.mean(np.abs(predictions['candidate'][groups==g]-y[groups==g])) for g in sorted(set(groups))])
    rng=np.random.default_rng(9821);boot=gains[rng.integers(0,len(gains),(s['bootstrap'],len(gains)))].mean(1)
    ci=np.quantile(boot,[.025,.975]).tolist()
    if classification_ok:
        passed=candidate['AUROC']>=s['auc'] and candidate['AUROC']-max(o['AUROC'] for o in others)>=s['auc_improvement'] and ci[0]>0
        endpoint='PREDECLARED_CLASSIFICATION'
    else:
        bestmae=min(o['MAE'] for o in others)
        passed=(candidate['Spearman'] is not None and candidate['Spearman']>=s['spearman'] and bestmae>0 and
                (bestmae-candidate['MAE'])/bestmae>=s['mae_improvement'] and ci[0]>0)
        endpoint='PREDECLARED_CONTINUOUS_FALLBACK'
    recordsout=[{**m,'seed':str(g),'delta':float(target),'candidate':float(p),
                 'baseline_predictions':{name:float(v[i]) for name,v in predictions.items() if name!='candidate'}}
                 for i,(m,g,target,p) in enumerate(zip(meta,groups,y,predictions['candidate']))]
    return {'status':'EVALUATED','prediction_gate_pass':bool(passed),'endpoint':endpoint,'independent_seed_n':n,
            'scores':scores,'paired_seed_MAE_gain_95ci':ci,'predictions':recordsout,
            'warning':'Features include extra matvec/block solve cost; no online-free oracle or speedup claim.'}
