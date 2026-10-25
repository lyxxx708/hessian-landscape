# Literature and disciplinary map (research navigation)

**Bibliography status:** names and threads summarized from conversation; this is NOT a verified reference list with DOI/page citations. Retrieve authoritative papers and check statements before publication.

## Objects and theory

1. **Neural curvature:** exact Hessian; outer-product Hessian/GGN; empirical Fisher; expected Fisher; natural gradient. Separate their rank and probabilistic meaning.
2. **Hessian spectral geometry:** near-zero bulk, outliers, negative curvature, symmetries, layer-wise localization, Hessian rank for deep linear networks.
3. **Gaussian graphical models:** conditional independence and precision sparsity of specified Gaussian variables; DAG moralization does not automatically hold for network parameter Hessians.
4. **Matrix-function decay:** banded SPD inverse estimates (Demko–Moss–Smith), localization results for sparse matrices / functions (Jaffard-type), matrix resolvents, spectral-gap/condition-number dependence.
5. **Structured curvature approximation:** Hessian-free Newton/CG, GGN, K-FAC, Shampoo, low-rank correction, Woodbury, banded LDLᵀ and MINRES.
6. **Overparameterized geometry:** deep linear factorization, gauge symmetries, quotient parameter spaces, Jacobian nullspace, finite-sample rank, effective model dimension.
7. **Dynamics / feature learning:** NTK/lazy versus rich regime; changing Hessian checkpoints; relation of spectral geometry to optimization, not a priori to generalization.
8. **Architecture effects:** ReLU masks, residual skips, normalization, attention: test rather than infer precision sparsity from forward computational topology.

## Paper clusters to verify

- J. Martens, Hessian-free optimization (2010).
- J. Martens and R. Grosse, K-FAC (2015); distinguish the block-diagonal and block-tridiagonal *approximations* from exact theorems.
- C. Botev and collaborators, GGN / block-diagonal curvature.
- Demko, Moss & Smith on decay rates for inverses of band matrices.
- S. Jaffard on localized matrices and inverse-closedness.
- Deep linear network Hessian rank papers, verify formula conditions especially nonzero residual and bottleneck dimensions.
- GMRF precision/moral graph theorem under linear-Gaussian assumptions.

## Open novelty question

A measured plateau shape in a damped inverse may be useful, but newness requires checking exact prior work on deep linear model identifiability, Fisher/K-FAC inverse structure, rank-one/low-rank perturbations and inverse covariance long-range coupling. Avoid phrases such as "first ever" until a verifiable prior-art table exists.
