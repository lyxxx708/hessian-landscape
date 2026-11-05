# GENESIS NEXT v1 — Implementation plan

**Goal:** A standalone, read-only follow-up kit for the frozen GENESIS v2 snapshot.
**Architecture:** Snapshot reanalysis first; separately frozen S1 checkpoint assays second. No upstream edits, S2 ingestion, training, scheduler, or automatic GitHub writes.
**Stack:** Python 3.11+, NumPy; PyTorch 2.10 environment for checkpoint assays; unittest; Windows PowerShell launcher.
**Spec:** EXPERIMENT_PLAN.md

## Tasks and verification
1. Test numerical identities: block-ray utility, nullspace-energy vs gradient action, spectral gain, CG matvec budget, covariance, zero-gradient handling; implement only after failing tests.
2. Test data boundaries: path traversal/overlap rejection, exact uint64-like seed strings, complete checkpoint aggregation, deduplication, manifest verification, S2 exclusion.
3. Build snapshot reanalysis and deterministic 80-state plan; validate against synthetic fixtures with original schemas.
4. Build frozen-source adapter and separately recorded FP64 assays. Verify source hashes, completed training receipt, dataset identity, independent reference, matvec/wall costs.
5. Build freeze/run/summarize/doctor and Windows wrapper; guard single-worker operation; subprocess timeout only affects this kit's child.
6. Run CPU unit/integration/demonstration tests; record untested Windows/CUDA/real-checkpoint boundaries; hash all deliverables and zip.

## Rulings
- This user requested a ready-to-run delivery rather than another approval round. New choices are proposals, not claims of prior registration.
- Original S2 remains sealed to this kit; follow-up uses S1 only and is exploratory. New confirmations must use a future independent holdout or untouched original S2 only for its original frozen endpoints.
- GPU assays require the existing worker already to be stopped through the owner's established workflow. This kit never stops it.
- Prior descriptive mechanism claims are not new discoveries: nullspace thresholds, coordinate covariance and tiny absolute gains must be tested explicitly.

## Final review rulings
- Found and fixed a qualification-boundary defect with a failing regression test: CPU receipts could qualify a CUDA panel, and missing CUDA memory data was accepted by default. Execution device is now frozen, receipts must match it, and CUDA requires measured allocated/reserved VRAM within target.
- Matched primary reference preserves original FP32 input values; native FP64 data is a separate quantization control.
- Checkpoint reader reconstructs exact S1-only measurement IDs; it never scans S2 result bodies.
- Dense eigensystems are reused across thresholds/dampings. Per-condition partials survive this kit's child timeout.
- No independent reviewer/subagent was available. A self-review plus fresh automated tests were performed; this is not represented as independent code review.
