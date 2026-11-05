"""Synthetic numerical demonstration, never labelled GENESIS scientific evidence."""
from pathlib import Path
import numpy as np
import torch
from .numerics import dense_geometry,ray_utility,gauge_diagnostic,hessian_diagnostics
from .solvers import cg,public_receipt
from .io_utils import write_json

def demonstrate(output):
    output=Path(output);rng=np.random.default_rng(73);A=rng.normal(size=(6,20));G=A.T@A
    g=A.T@rng.normal(size=6);groups=[np.arange(0,10),np.arange(10,20)];lam=.001*np.linalg.eigvalsh(G).max();Q=G+lam*np.eye(20)
    x=-np.linalg.solve(Q,g);b=np.concatenate([-np.linalg.solve(Q[np.ix_(j,j)],g[j]) for j in groups])
    utility=ray_utility(Q,g,x,b);geometry=dense_geometry(G,g,lam,groups)
    t=np.r_[np.full(10,10.),np.full(10,.1)];gauge=gauge_diagnostic(G,g,lam,groups,t)
    Qt=torch.tensor(Q,dtype=torch.float64);gt=torch.tensor(g,dtype=torch.float64)
    curve=[]
    for k in [1,2,4,8,16,32]:
        d,r=cg(lambda v:Qt@v,-gt,max_iter=k)
        gain=float(-gt@d-.5*d@r['Qx']);curve.append({'steps':k,'gain_ratio':gain/utility['F_star'],**public_receipt(r)})
    result={'evidence_class':'SYNTHETIC_SOFTWARE_DEMONSTRATION_NOT_RESEARCH_DATA',
            'utility':utility,'geometry':geometry,'gauge':gauge,'cg_curve':curve,
            'hessian_tiny_negative_example':hessian_diagnostics(np.diag([0.,1.]),np.diag([-1e-12,1.]))}
    write_json(output/'SYNTHETIC_DEMO.json',result)
    return {'status':'SYNTHETIC_DEMO_COMPLETED','output':str(output/'SYNTHETIC_DEMO.json'),
            'scientific_validation':False,'null_energy_fraction':geometry['null_energy_fraction'],
            'gradient_null_fraction':geometry['gradient_null_fraction'],
            'gauge_covariance_error':gauge['covariant_direction_error']}
