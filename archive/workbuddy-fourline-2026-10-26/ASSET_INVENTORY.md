# Asset inventory — what is present, and what it is

This inventory replaces the earlier version, which recorded the raw payload as
unavailable. It is now **present, verified and published**.

## 1. Present and published

| Asset | Location | Bytes | State |
| --- | --- | --- | --- |
| Original research package | Release `archive-20261026` | 2,089,046,079 | `PAYLOAD_HASH_VERIFIED`, see `INTEGRITY_REPORT.md` |
| Package manifest | inside package, `MANIFEST.csv` | 325,349 | SHA-256 verified, binding verified |
| Manifest binding | inside package, `MANIFEST.sha256` | 80 | verified against manifest |
| Package verification record | inside package, `PACKAGE_VERIFICATION.json` | 1,223 | 2026-10-25 record, status `PASS` |
| Package scope declaration | inside package, `COLLECTION_SCOPE.json` | 5,924 | reconciled, see `INTEGRITY_REPORT.md` §6 |
| Scientific report (Markdown) | `EXPERIMENT_REPORT.md` here + inside package | 38,095 | byte-identical to packaged copy |
| Scientific report (PDF) | inside package, `EXPERIMENT_REPORT.pdf` | 364,574 | SHA-256 verified |
| Tables (15 CSV) | inside package, `tables/` | 34,201 | verified |
| Figures (8 PDF/SVG) | inside package, `figures/` | 46,006 | verified |

## 2. What is inside the package — by class

Classification is path- and manifest-derived. A file's class is not inferred from its
name alone; where a class is ambiguous the conservative label is used.

| Class | What it covers | Scale |
| --- | --- | --- |
| `PROTOCOL` | `research_design_v1..v3`, `science_v*/PLAN.json`, `PROTOCOL.md`, `METHODS_ADDENDUM.md`, `DECISION_CRITERIA` | 43 + 14 + 4 + 2 + 14 design files |
| `SOURCE_CODE` | `science_v4/*.py`, `science_v5..v9`, `bridge/`, `runner/`, `contracts/`, `scripts/`, `tools/`, `tests/` | 257 `.py`, 82 `.mjs`, 26 `.ps1` |
| `EXECUTION_RECORD` | `records/science_v*`, `records/supervision_20261022`, terminal receipts, `CONTROL.json` | 172 + 12 + 35 + 47 + 8 + 27 + 104 |
| `ORIGINAL_EVIDENCE` | raw numerical bundles `*/bundle/raw.npz`, `welch_spectrum.json`, `first_crossing_exact.json`, `.bin` fixtures | 14 `.npz`, 2.08 GB |
| `FAILED_RUN` | `records/**` entries carrying `FAIL` / `STOP` outcomes, `BATCH_RESULT.json` failure states | preserved in place |
| `SUPERSEDED_VERSION` | `science_v9/genesis_feasibility_v3r3..v3r14`, `science_v7/anti_q4h_d7r1..r3`, `science_v8/..._v1`, `..._v2` | 14 GENESIS revisions, 3 Q4H repair rounds |
| `DERIVED_REPORT` | `EXPERIMENT_REPORT.md`/`.pdf`, `tables/`, `figures/` | 27 entries |
| `CONFIRMATORY_PROTECTED` | none present | 0 |
| `EXCLUDED_PRIVATE` | not in package — see §4 | — |

Negative results are **not** filtered out. The package carries the failures that the
report's narrative depends on: the `PILOT_EXECUTION_FAILED` initial job, the 0/6 depth-8
GENESIS qualification, the 25,074 rejected NAO surrogate proposals, the 0/84 Anti-Slowing
joint-condition passes, and the 0-witness signed-Sokal finite grid.

## 3. Research-line mapping

Derived by path prefix over `MANIFEST.csv`. No file is assigned to a line by content
inference.

| Line | Files | Bytes | Notes |
| --- | --- | --- | --- |
| `CROSS_LINE` | 214 | 2,114,349,104 | `science_v4` / `records/science_v4` — one authoritative batch executing all four lines; holds the 1.87 GB `anti_slowing` raw bundle |
| `GENESIS` | 223 | 1,700,909 | `science_v9` (v3 … v3r15), `records/science_v9`, `experiments/genesis` |
| `NAO_V3` | 108 | 5,049,877 | `science_v6` surrogate qualification rounds, `records/science_v6` |
| `ANTI_SLOWING` | 123 | 2,595,035 | `science_v7/anti_*` Q4H D5–D7, `records/science_v7/anti_*` |
| `SIGNED_SOKAL` | 54 | 3,201,168 | `science_v8` exact finite grids v1–v3 |
| `SHARED_INFRASTRUCTURE` | 1,302 | 14,183,026 | `bridge`, `runner`, `contracts`, `scripts`, `tools`, `tests`, `docs`, `packaging_tools`, `conversation_reports` |
| **Total** | **2,024** | **2,141,079,119** | matches verified content totals |

The byte distribution is dominated by one artefact: the Anti-Slowing raw trajectory bundle
is 1.87 GB of the 2.14 GB total. Any statement about "2.14 GB of data" is really a
statement about that one array file plus 2,023 small files totalling 22 MB.

## 4. Excluded, and why

Excluded by the package's own `COLLECTION_SCOPE.json`, and independently confirmed absent:

| Excluded | Reason |
| --- | --- |
| `E:\WorkBuddyProject\.venvs\**` | virtual environments; reproducible, not evidence |
| `E:\WorkBuddyProject\node_modules\**` | dependency cache |
| `E:\WorkBuddyProject\.git\**` | object database |
| `E:\WorkBuddyProject\data\` | declared out of scope |
| `D008`/`D009`, confirmatory, holdout, sealed, frozen subtrees | protocol-forbidden; 0 path hits |
| credentials, tokens, keys, cookies, account DBs | 0 detected in content scan |
| unrelated Codex session trees outside `E:\WorkBuddyProject` | outside scope |

`E:\WorkBuddyProject` currently holds 33,442 files / 10,067,570,810 bytes. That is **not**
the archive's denominator — roughly 7.9 GB of it is the excluded runtime cache above. The
denominator is the 50 declared roots: 1,984 files / 2,139,736,566 bytes, all present.

The 13 manifest rows beyond the declared scope are packaging provenance
(`packaging_tools/` + `conversation_reports/`), retained as the audit trail for how the
report and package were produced. Reconciliation is exact; see
`INTEGRITY_REPORT.md` §6.

## 5. Availability of the original source tree

`E:\WorkBuddyProject` is present on the operator machine and holds live working state
beyond the sealed package. The package is a **snapshot**, not a mirror: later edits to the
source tree are not in it, and the package must never be used to overwrite the source tree.
Restoring is one-directional — package out, never source over package.

## 6. Completion condition

| Requirement | Status |
| --- | --- |
| Original package located and identified | met |
| Every member matches manifest with path, bytes, SHA-256 | met — 2,024/2,024 |
| Manifest self-binding verified | met |
| Package structure safe (traversal/dup/symlink) | met — 0/0/0 |
| Exclusions recorded with reasons | met — `EXCLUSION_REPORT.md` |
| Public-repo privacy scan complete | met — with stated heuristic limits |
| Payload uploaded to downloadable durable store | met — Release asset |
| Independent re-download and hash comparison | recorded in `INTEGRITY_REPORT.md` |
| Remote commit and asset linked from a verifiable index | met — `ARCHIVE_INDEX.json`, `RELEASE_ASSETS.md` |

Level attained: **`PAYLOAD_HASH_VERIFIED`**. It is not `FULL_ARCHIVE_VERIFIED` unless
`INTEGRITY_REPORT.md` §7 records a completed clean re-download.