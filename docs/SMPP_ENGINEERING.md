# Algorithm engineering (E-series) — planned, not delivered

## Conditional architecture decisions

- **Bandwidth:** choose tri/penta/other from verified target *curvature or preconditioner* off-band energy and actual solver residual; skip topology alone is not proof.
- **Damping λ:** 1e-4 was proposed historically, not validated universally. Needs condition/SPD monitoring and step acceptance.
- **K=1 + EMA:** a research hypothesis, not a proven estimator. Compare HVP estimators to explicit small-model blocks and variance versus K.
- **Curvature:** exact H is often indefinite; SPD-only Cholesky can be applied to GGN+λI or sufficiently shifted H, not blindly to arbitrary H.

## Engineering tickets

| Ticket | Responsibility | Verification |
|---|---|---|
| E00 | optimizer API, state serialization, controls and reproducible logging | resume reproducibility & AdamW baseline |
| E01-A | define loss scaling, curvature object, probe estimator, update formula and detaches | mathematical review |
| E01-B | estimate D0/D1/D2 block curvature from HVP or GGN-vector product | compare with explicit target blocks, bias/variance |
| E01-C | block tri/penta factorize/solve with fallback | relative solve residual, symmetry, SPD/indefinite handling |
| E01-D | controlled toy→CIFAR→ImageNet training benchmarks | time-to-accuracy, multiple seeds, confidence intervals |
| E02-A | fused kernel performance model, tensor layouts, staging feasibility | measured bottleneck and memory traffic |
| E02-B | implement kernel vs PyTorch gold baseline | dtype/size correctness, runtime and OOM checks |

For fixed block size b and bandwidth w, banded factorization generally costs O(L w² b³), not O(total parameters) uniformly when blocks grow. A Hutchinson vector product does not magically construct a dense b×b block with negligible error; estimate/complexity carefully.

## Suggested performance baseline

AdamW, original MPP-H (if source obtained), SMPP tri/penta, and band+low-rank variants; identical training budgets, hardware, warmup, learning-rate tuning policy and target accuracy. Measure wall-clock time and memory, not just iteration count.

**Status:** API/solver/kernel code from historical Gemini reports is not present in repository and was not located in accessible assets. Do not claim it exists.
