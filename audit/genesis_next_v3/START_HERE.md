# GENESIS NEXT v3 — evidence package (Draft)

**Evidence class:** `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`. DLN only, CPU FP64, no new training.
The package holds 38 DLN checkpoint states × 3 dampings = 114 conditions (19 training seeds, 4 settings), drawn from 80 planned states / 240 conditions. The remaining 42 states / 126 conditions are `SOURCE_NOT_READY` and stay in the denominator.

## Contents
| path | what |
|---|---|
| `run_v3/` | Main v3 run: Exp V (why train-selected second-order steps hurt held-out loss), Exp B (Full CG vs optimized exact Block-GGN cost), V4 (T512 intervention). |
| `run_v3/SCIENTIFIC_VERDICT.md` | v3 verdict, outcome labels, limitations. |
| `run_v3/PROTOCOL_LOCK.json`, `RUN_PLAN.json` | Frozen protocol (freeze_sha `0b168ec5…`) and the 38-state plan. |
| `run_v3/results/*.json` | Raw per-state records: qualification, Exp B quality and timing samples with contention, V4. |
| `run_v3/alpha_grid/*.jsonl` | Complete α-grid curves (11 α × pools T32/T512/T4096/V1024/E8192/Test1024/V32 + native FP64, with sign bounds and sub-batch groups). |
| `run_v3/slopes/*.jsonl` | Directional slopes and curvatures (JVP and closed form). |
| `run_v3/qualification/` | Pilot reproduction of NEXT v2 (gate 2), unit-test log (gate 3), superseded pilot and unfrozen smoke run. None of these enter the tables. |
| `run_v3/*.csv`, `*.jsonl`, `ANALYSIS_SUMMARY.json` | Frozen-analysis tables. |
| `run_v3/EXECUTION_LEDGER.jsonl`, `logs/` | Every state exit (38× `EXIT_0`). |
| `run_A1_population_oracle/` | Addendum A1: exact analytic population-risk oracle (freeze_sha `1a0b6770…`). Its verdict is in `ORACLE_VERDICT.md`. |
| `run_A1_population_oracle/curves/*.jsonl` | Full step curves: population risk, T32, T512 and E8192 loss on 242 α in [0, 30] per direction. |
| `source/` | Executed source: `genesis_next_v3/`, `scripts/`, `tests/`, `configs/`, `docs/` (incl. `design_input/`) and `oracle/`. |
| `environment/` | Platform and package versions. |
| `audit_tools/package.py` | How this package was assembled (byte-identical copies, verified). |
| `FILE_MANIFEST_SHA256.csv` | SHA-256 of every file. `.gitattributes` disables line-ending conversion, so the bytes match. |

## Headline results (details and caveats in the two verdict files)
* **Exp V.** Train-selected (T32) steps worsen loss on new data:
  * E8192 gain is negative in 102/114 (Full), 106/114 (Block) and 112/114 (CG8) conditions.
  * The dominant label is step overshoot (~90%); first-order conflict accounts for ~10%.
* **A1 population oracle.** This is an exact population risk, so it involves no sampling noise:
  * The T32-selected step is a median ~14× the population-optimal step.
  * It raises the true population risk in 99/109 qualified Full conditions.
  * The population sign agrees with the v3 E8192 sign in 100% of conditions.
  * T512 selection lands within a factor ~1 of α_pop.
  * Same-batch α selection overshoots even at T512.
  * Under optimal population steps the T512 direction attains ~7× the gain of the T32 direction. This qualifies the v3 V4 reading.
* **Exp B.** Optimized exact Block erases the historical CG cost advantage:
  * At equal quality, CG/Block cost is about 1.0–1.06 (raw policy).
  * The historical ratio came from the padded AD block solver, which is ~1541× slower than the Kronecker-direct solver.
  * Exact Block reaches 0.99·F* in only 1/114 conditions.

## Verify
* Recompute the hashes against `FILE_MANIFEST_SHA256.csv`.
* Re-run the tables:
  * `python source/scripts/analyze.py run_v3`
  * `python source/oracle/analyze_oracle.py run_A1_population_oracle`

  Both scripts read the paths fixed in their headers; see `run_v3/README_REPRODUCE.md`.
* A full re-execution needs the local v2 run (checkpoints, data) and its executed source. These are not included (see `EXCLUSIONS.md`).
