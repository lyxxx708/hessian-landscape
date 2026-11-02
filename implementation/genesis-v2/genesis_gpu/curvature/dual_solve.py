import torch


def dual_solve(J,W,rhs,damping):
    """Small-output exact Woodbury oracle; only within prequalified memory limits."""
    if damping<=0 or W.shape!=(len(J),len(J)) or J.shape[1]!=len(rhs):
        raise ValueError('Invalid dual solve inputs')
    eig,V=torch.linalg.eigh((W+W.T)/2)
    if eig.min()<-1e-10*max(1.,float(eig.abs().max())):
        raise ValueError('Output loss Hessian not PSD')
    A=(eig.clamp_min(0).sqrt()[:,None]*V.T)@J
    middle=A@A.T+damping*torch.eye(len(A),device=A.device,dtype=A.dtype)
    x=(rhs-A.T@torch.linalg.solve(middle,A@rhs))/damping
    residual=(J.T@W@(J@x)+damping*x-rhs).norm()/rhs.norm().clamp_min(1e-30)
    if not torch.isfinite(x).all() or residual>1e-5:
        raise ArithmeticError('Dual solution failed independent primal residual check')
    return x
