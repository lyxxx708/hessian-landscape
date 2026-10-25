# WorkBuddy four-line scientific asset archive — 2026-10-26

**Integrity level: `PAYLOAD_HASH_VERIFIED`** — the original 2.089 GB package was found,
byte-verified against its own manifest, audited for publication safety, and uploaded as a
GitHub Release asset. The remote round-trip re-download verdict is recorded in
[INTEGRITY_REPORT.md](INTEGRITY_REPORT.md); this directory does not claim
`FULL_ARCHIVE_VERIFIED` unless that file says so.

This directory preserves the 2026-10-26 **WorkBuddy 四线研究全阶段实验实施与结果报告**
and, for the first time, the underlying raw research payload it describes.

## The payload

| | |
| --- | --- |
| Package | `WorkBuddy_AllStages_20261026.zip` |
| Bytes | **2,089,046,079** |
| SHA-256 | `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` |
| Members | 2,026 (2,024 content + `MANIFEST.csv` + `MANIFEST.sha256`) |
| Uncompressed | 2,141,079,119 bytes |
| Download | [Release `archive-20261026`](https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026) |
| Transport | GitHub Release asset, byte-exact, single part (no reassembly) |

Start at [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md) to recover and verify it on a new
machine. Verify with the bundled `tools/verify_package.py` — standard library only, and it
has been negatively tested (a single flipped digest in the manifest does fail it).

## Documents here

| File | What it is | Evidentiary class |
| --- | --- | --- |
| `EXPERIMENT_REPORT.md` | User-supplied report, byte-identical to the packaged copy | `DERIVED_REPORT` |
| `INTEGRITY_REPORT.md` | Everything measured about the package, with numbers | `ORIGINAL_EVIDENCE` (about the package) |
| `EXCLUSION_REPORT.md` | Publication-safety audit, exclusions, residual risk | `ORIGINAL_EVIDENCE` |
| `REPRODUCTION_GUIDE.md` | Download → verify → extract → locate | instructions |
| `RELEASE_ASSETS.md` | Transport decision, asset record, re-issue policy | `EXECUTION_RECORD` |
| `ARCHIVE_INDEX.json` | Machine-readable version, hashes, counts, line mapping | index |
| `FILE_MANIFEST.csv` | All 2,024 entries: path, bytes, SHA-256, phase root, relative path | index |
| `CHECKSUMS.sha256` | Outer package + manifest + binding | index |
| `ASSET_INVENTORY.md` | What is present, where it came from, what is excluded | `DERIVED_REPORT` |
| `SOURCE_INDEX.tsv` | Report-cited sources S01–S19 → archive paths | index |
| `SCIENTIFIC_STATE.md` | Four-line scientific status, unchanged | `DERIVED_REPORT` |
| `TRANSFER_RUNBOOK.md` | Superseded transfer procedure, kept as history | `SUPERSEDED_VERSION` |
| `tools/verify_package.py` | Standalone verifier, negatively tested | `SOURCE_CODE` |

## Scientific boundary — do not soften this

The report records synthetic pilots, engineering audits and qualification failures. It does
**not** establish a confirmatory mechanism on any of the four lines.

- GENESIS: no qualified deep endpoint; v3r15 has not run its 36-fit pilot.
- NAO V3: current candidate has not stably beaten strong baselines; the mandatory
  multi-scale surrogate qualification failed.
- Anti-Slowing: the pre-registered local-acceleration condition did not pass; historical
  state-null scientific calibration is unclosed.
- signed-Sokal: one boundary counterexample exists; the 81-case three-state finite grid
  found no target witness.

Failed, superseded and negative results are preserved verbatim — including
`genesis_feasibility_v3r3..v3r14` and `anti_q4h_d7r1..r3`. Archiving is a custody
milestone, not a discovery.

## Privacy

The repository is public. The package was scanned for credentials and protected subtrees
before publication; findings, exclusions and the one accepted disclosure are recorded in
[EXCLUSION_REPORT.md](EXCLUSION_REPORT.md). No `D008`/`D009`, confirmatory, holdout,
sealed or frozen material is present, consistent with
`science_v4/AUTHORIZATION.json` (`confirmatory_authorized: false`).

## What changed in this revision

The previous revision of this directory stated the raw payload was "not present here" and
uploaded only documentary material. That was accurate for an environment without access to
`E:\WorkBuddyProject`. This revision locates the original package, verifies it, audits it
and publishes it. `TRANSFER_RUNBOOK.md` is retained unedited as the record of the earlier,
incomplete state — it is superseded by the documents above.

The existing GENESIS-only documentary material in `docs/`, `archive/`, `scripts/` and
`tests/` is untouched.