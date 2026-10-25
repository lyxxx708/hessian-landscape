# Scientific state — authority and scope

**Snapshot date:** 2026-10-26. **Authority class:** documentary reconstruction from user-provided text. No fresh execution.

## Workstreams

| Stream | Historical stage | What is actually supported | Status for next decision |
|---|---|---|---|
| DLN numerical forensics | Phase I–V | Reports claim fp64 CPU solve and block-distance spectra; numerical values are transcribed | DOCUMENTARY_ONLY; reconcile contradictions |
| Long-range plateau | Phase V/V-B Rev3.4 | Rank-one scalar-chain analytic formula is checkable; near-zero exact–GGN gap and spectral ablations reported | THEORY BASELINE + UNVERIFIED EXPERIMENT |
| Matrix geometry arbitration | Phase VI Rev3/Rev4 | Chain Kronecker lost to block permutation on cited distance; exact shifted Hessian fails chosen SPD gate at λ=0.1 | APPROVED FAIL (historical), useful negative result |
| Phase VII / Path B | Planned | GGN + positive damping, Chain/Global/Mixed fit with null controls | NOT RUN |
| SMPP optimizer and fused CUDA | Planned design | No working original implementation or training benchmark supplied | NOT IMPLEMENTED / NOT VERIFIED |

## Claims that must be narrowed

1. **No universal theorem of long-range plateau has been established.** A scalar toy establishes existence of one flat-distance example; claims for DLN/ReLU/ResNet are hypotheses pending conditions and replications.
2. **The exact Hessian is not always indefinite.** Some initialization checkpoints are reported indefinite. At zero residual for squared loss the exact Hessian equals GGN and is PSD; a λ-dependent check is needed.
3. **Nullspace is not automatically a small-rank correction.** The nullspace projector may have high rank and dense cross-layer entries.
4. **Classical inverse-decay theory is conditional, not globally disproved.** SPD-based statements do not apply to an indefinite object; other resolvent and inverse-decay results may apply under suitable spectral gap and bandedness hypotheses.
5. **Earlier assistant PASS decisions are not independent test results.** Critical metrics are still inconsistent; see CLAIMS_AND_AUDIT.md.

## Current defensible project positioning

A structured investigation of when damped inverse Hessian / GGN layer-block couplings decay, exhibit a nonzero plateau, or become misleading under finite precision, damping and rank deficiency; and whether banded-plus-global-low-rank approximations improve optimization.

## Resume conditions

Before treating numerical findings as verified, obtain original hashes and raw executable code; rerun tests and record H versus GGN rank, full eigenvalue spectrum, condition numbers of H+λI, solver forward error relative to high-precision baseline, normalized block curves and energy mass from the same run.

**Do not merge historical GENESIS / Hessian claims with unrelated NAO "Genesis Migration" program assets; matching names are not sufficient evidence of identity.**
