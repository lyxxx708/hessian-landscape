# Reproduction guide — recovering this archive on a new machine

This guide gets you from "empty machine + this repository" to "byte-verified local copy
of every publishable historical research asset, with failures and retractions intact".

It covers **recovery and verification only**. Nothing here re-runs a scientific job,
re-derives a result, or licenses a new claim. See §7 for that boundary.

## 1. Prerequisites

- `git` ≥ 2.30
- `python` ≥ 3.9 (standard library only for verification — no NumPy needed to check hashes)
- ~2.1 GB free disk for the package, plus ~2.2 GB if you extract it
- Network access to `github.com`

You do **not** need Git LFS. The payload is a GitHub Release asset, not an LFS object.

## 2. Get the metadata

```bash
git clone https://github.com/lyxxx708/hessian-landscape.git
cd hessian-landscape
git checkout archive/workbuddy-fourline-20261026
```

If PR #4 has not been merged, the branch above is still the authoritative ref. `main`
carries the GENESIS-only documentary history and does **not** yet contain this archive.

## 3. Download the package

```bash
gh release download archive-20261026 \
  --repo lyxxx708/hessian-landscape \
  --pattern 'WorkBuddy_AllStages_20261026.zip'
```

Without `gh`:

```
https://github.com/lyxxx708/hessian-landscape/releases/download/archive-20261026/WorkBuddy_AllStages_20261026.zip
```

Expected size: **2,089,046,079 bytes** exactly.

## 4. Verify before trusting anything

```bash
sha256sum WorkBuddy_AllStages_20261026.zip
# 290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f
```

If that line does not match, **stop**. Do not extract, do not cite, do not build on it.
Re-download; a partial or truncated asset is the most common failure and it will still
unzip "successfully" for early entries.

Then verify the manifest binding and every member:

```bash
python archive/workbuddy-fourline-2026-10-26/tools/verify_package.py \
  --zip WorkBuddy_AllStages_20261026.zip
```

Expected output:

```
outer bytes     2089046079        OK
outer sha256    290b8429...ebf1f  OK
manifest        f24b7911...01836  OK
members         2026
content members 2024
content bytes   2141079119        OK
size mismatch   0
hash mismatch   0
missing         0
extra           0
RESULT          PACKAGE_VERIFIED
```

## 5. Extract with a path-safety guard

The package was audited to contain zero `..` segments, zero absolute paths, zero
duplicate members and zero symlinks. Verify it yourself before extracting — the guard is
cheap and the audit is only as good as the bytes you actually downloaded.

```bash
python - <<'PY'
import zipfile, sys
z = zipfile.ZipFile("WorkBuddy_AllStages_20261026.zip")
bad = [n for n in z.namelist()
       if n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/")]
print("unsafe entries:", len(bad))
sys.exit(1 if bad else 0)
PY
```

Only if that prints `0`:

```bash
unzip -q WorkBuddy_AllStages_20261026.zip -d payload
```

## 6. Find things

The extracted tree is rooted at `project/`, which mirrors `E:\WorkBuddyProject`:

| You want | Look at |
| --- | --- |
| The scientific report | `COLLECTION_SCOPE.json`'s sibling `EXPERIMENT_REPORT.md`, `figures/`, `tables/` (package root, `phase_root=new_report_and_tables`) |
| Four-line protocols and plans | `project/science_v4/PLAN.json`, `project/research_design_v*/`, `project/science_v9/genesis_feasibility_v3r15/PROTOCOL.md` |
| Terminal receipts / outcomes | `project/records/science_v*/` — `BATCH_RESULT.json`, `FINAL_ASSESSMENT_*.json`, `RUN_TERMINAL_RECEIPT.json`, `FINAL_DISPOSITION.json` |
| Raw numerical arrays | `project/records/science_v4/20261022T085915Z_c62e709c/*/bundle/raw.npz` (largest: `anti_slowing` bundle, 1.87 GB) |
| Execution logs | `project/records/**/*.log`, 219 files |
| Failed and superseded runs | `project/science_v9/genesis_feasibility_v3r3..v3r14/` (superseded), `project/science_v7/anti_q4h_d7r1..r3/` (repair rounds) |
| Governance / authorization | `project/science_v4/AUTHORIZATION.json`, `project/RESEARCH_PROTOCOL.md`, `project/DECISION_CRITERIA.md` |
| Packaging provenance | `packaging_tools/` (inventory + rendering scripts), `conversation_reports/` |
| Report's own cited sources S01–S19 | `SOURCE_INDEX.tsv` → `original_project_path` column; all 19 resolve into `project/` |

For a machine-readable map, use `FILE_MANIFEST.csv` in this directory: it carries the
package path, byte size, SHA-256, `phase_root`, and a `relative_path` with the `project/`
prefix stripped so you can join it directly against the extracted tree.

`ARCHIVE_INDEX.json` carries the per-research-line file/byte mapping and the transport
record.

## 7. Rebuild the environment (optional, and separate from verification)

Verification in §4–§6 requires only the Python standard library. To actually execute the
study code you additionally need the pinned environment:

```bash
pip install -r project/bootstrap_v2/verified-science-requirements.txt
```

`project/science_v4/ENVIRONMENT_LOCK.json` and
`project/bootstrap_v2/VERIFIED_WHEEL_MANIFEST.json` record the intended interpreter and
wheel hashes. Note the recorded discrepancy from the report: the GENESIS v3r15 frozen
runtime manifest matched **28/30** entries, with two core Python runtime hashes
differing. A qualified environment is therefore **not** byte-identical to the original
execution host. Read `SCIENTIFIC_STATE.md` before drawing any inference from a re-run.

## 8. Boundaries — read this before using the data

Recovering bytes does **not** do any of the following:

- It does not establish that any hypothesis in the report is confirmed.
- It does not authorize a re-run of frozen protocols, `D008`/`D009`, confirmatory or
  holdout work. `science_v4/AUTHORIZATION.json` sets
  `confirmatory_authorized: false` and `historical_data_authorized: false`.
- It does not repair the historical failures. `FAIL`, `STOP`, `REVISE` and
  `SOURCE_MISSING` outcomes are preserved as recorded.
- It does not validate that the report's numbers were correctly computed — only that the
  bytes carrying those numbers are intact and unmodified.

The scientific status of the four lines is stated in `SCIENTIFIC_STATE.md` and is
unchanged by this archiving work. In summary: no generalisable confirmatory mechanism has
been established on any of the four lines, and several lines carry unresolved
qualification failures.

## 9. If verification fails

| Symptom | Meaning | Action |
| --- | --- | --- |
| Outer hash differs, size differs | Truncated/corrupted download | Re-download; do not proceed |
| Outer hash OK, member mismatches > 0 | Package bytes changed in transit or storage | Report it; do not use |
| `manifest` hash differs | `MANIFEST.csv` altered | Report it; the manifest is the authority |
| Extraction guard prints > 0 unsafe | Malicious/repacked archive | Do not extract |
| Release asset 404 | Release or asset removed | Check `RELEASE_ASSETS.md` for the recorded asset id and re-resolve |