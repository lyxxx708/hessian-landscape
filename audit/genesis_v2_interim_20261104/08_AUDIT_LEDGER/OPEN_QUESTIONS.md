# Open questions

Each item is unresolved at snapshot time. None has been answered by assertion.

1. Does the FP32 false-valid trajectory change S1 U aggregates or the S1 predictor fit? Not analysed. The owner decided the analysis is independent of the pipeline and runs after S1 data is complete, with three inputs (original, rows excluded, FP64 values substituted). It cannot alter frozen results.
2. Are structure metrics, probe-based intervals and mechanism records numerically sound? Not audited. The first raw audit target would be `probe_artifacts_*.jsonl` and `structure_records.jsonl`.
3. How much of γ=0.001 is genuinely unmeasurable in v2 versus a solver artifact? Dense references exist for small DLN cases (offline), but only as a diagnostic, not in the protocol.
4. Do the non-DLN families behave like DLN at trained, low-gradient states? No trained non-DLN state exists; the offline v2.1 evidence uses one one-step preflight state per family.
5. What are real CUDA cost, memory and throughput for plain FP64 CG on the Transformer? Unmeasured. A CUDA G0 needs a cooperative v2 pause, which has not been taken.
6. Why does the DLN data fingerprint depend on thread count? Observed (2, 3, 4, 8, default threads give different values; 2 and 4 agree on one seed but not the other), cause not isolated.
7. Is the matched-cost CG baseline too weak to discriminate? It converged using 9–14 matvecs in offline MLP, ResNet and Transformer tests; DLN budgets were larger. Impact on U and P unknown.
8. ResNet and Transformer `group_for`: do they also repeat partitions between coarse and fine? Not reviewed.
9. The coarse/fine v2 δ is identical for DLN; do structure probes on fine rows differ (different random draws)? Not compared.
10. Will the failed S1 setting (`dln_d4_w16_orthogonal_balanced_c1`, 4 of 5 seeds) change setting-level statistics? That depends on the frozen analysis' handling of missing seeds; not checked.
