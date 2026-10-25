# WorkBuddy four-line scientific asset archive — 2026-10-26

**Integrity level: `FULL_ARCHIVE_VERIFIED`**

All 63 released chunks re-downloaded through the public url, each chunk's server-declared and locally recomputed sha-256 matched, reassembly reproduced the 2,089,046,079-byte package digest, and every one of the 2,024 content members re-verified against the manifest carried inside the download.

Measured evidence — not transcription — is in
[INTEGRITY_REPORT.md](INTEGRITY_REPORT.md) and [RELEASE_ASSETS.md](RELEASE_ASSETS.md).

This directory preserves the 2026-10-26 **WorkBuddy 四线研究全阶段实验实施与结果报告**
and, for the first time, the underlying raw research payload it describes.

## The payload

| | |
| --- | --- |
| Package | `WorkBuddy_AllStages_20261026.zip` |
| Bytes | **2,089,046,079** |
| SHA-256 | `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` |
| Members | 2,026 (2,024 content + `MANIFEST.csv` + `MANIFEST.sha256`) |
| Uncompressed | 2,141,079,119 bytes (the 2,024 content members) |
| Download | [Release `archive-20261026`](https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026) |
| Transport | GitHub Release assets, **63 chunks of 32 MiB**, byte-exact, concatenated to reassemble |

The payload travels as 63 chunks because this host's uplink measured ~117 KB/s per stream,
and a single POST on this link does not survive much past ~20 minutes. A 400 MiB part needs
~57 minutes and was reset at 22m13s having stored ~133 MB, so the transfer can never finish
that way — see the failure table in [RELEASE_ASSETS.md](RELEASE_ASSETS.md). At 32 MiB a chunk
completes in ~4.7 minutes single-stream, leaving 4× headroom under the connection limit. Each
chunk carries its own SHA-256 and each is separately resumable.

Concurrency was raised only as far as the endpoint tolerated. A 16-way run produced 14
`HTTP 404` failures after full 32 MiB transfers — the local proxy's TLS connection pool was
exhausted, not the uplink — so the run that actually completed all 63 chunks used 3–4
concurrent streams. Measured result: **69 minutes end-to-end, ~492 KB/s aggregate**, at
~134 KB/s median per stream. The 762 KB/s figure in `RELEASE_ASSETS.md` is a short-burst
probe throughput, not what the full transfer sustained; the two are recorded separately so
neither is mistaken for the other.

Reassembly is one `cat` in lexicographic order (zero-padded names) and reproduces the digest
above exactly. See [RELEASE_ASSETS.md](RELEASE_ASSETS.md) for the chunk table.

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