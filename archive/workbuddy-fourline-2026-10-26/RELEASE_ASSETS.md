# Release assets — what is actually downloadable

Transport decision, recorded with the reasons, because "upload succeeded" is a claim
that has to be checkable.

## Why a Release asset and not LFS

| Option | Measured constraint | Verdict |
| --- | --- | --- |
| Plain Git blob | 100 MiB per file hard limit | Impossible — largest member is 1.87 GB |
| Git LFS | GitHub free tier: 1 GiB storage + 1 GiB/month egress | Impossible — package is 2.089 GB, and a clone would exhaust egress immediately |
| **GitHub Release asset** | 2 GiB per asset; no LFS quota; plain HTTPS download | **Chosen** — package is 1,992.27 MiB, fits with ~56 MiB headroom |

LFS was probed live before deciding: the batch endpoint answered `HTTP 200` and issued
upload and verify actions, so LFS is *technically* enabled on this repository. It was
rejected on **quota**, not on availability. Recording that distinction matters — a future
maintainer with an LFS data pack could switch transports without re-auditing capability.

Because the package fits in one asset, **there are no split parts**. No part ordering, no
reassembly step, and no chance of a missing chunk. The SHA-256 of the single asset is
the SHA-256 of the original package.

## The asset

| Field | Value |
| --- | --- |
| Name | `WorkBuddy_AllStages_20261026.zip` |
| Release tag | `archive-20261026` |
| Release URL | https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026 |
| Bytes | **2,089,046,079** |
| SHA-256 | `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` |
| Content | 2,026 members — 2,024 content + `MANIFEST.csv` + `MANIFEST.sha256` |
| Uncompressed content bytes | 2,141,079,119 |

Direct download:

```
https://github.com/lyxxx708/hessian-landscape/releases/download/archive-20261026/WorkBuddy_AllStages_20261026.zip
```

## Byte-exactness

The uploaded file **is** the original package. It was not re-zipped, re-compressed, or
re-packed. Rationale: the package had already been proven internally closed — all 2,024
members match the manifest with zero mismatches — so re-archiving would have produced a
new digest for identical content and destroyed the ability to compare against the
`PACKAGE_VERIFICATION.json` record from 2026-10-25. Preserving the original bytes keeps
two independent verifications pointing at the same object.

`recompressed: false` and `byte_exact_preserved: true` in `ARCHIVE_INDEX.json` record
this.

## Verification record

The download-verify step is documented with its outcome in `INTEGRITY_REPORT.md` §7–§8
and summarised in `README.md` under "Integrity level". Read the recorded level there
rather than assuming this file's existence implies a completed round trip.

The command that produces the authoritative answer, runnable by anyone:

```bash
gh release download archive-20261026 --repo lyxxx708/hessian-landscape \
  --pattern 'WorkBuddy_AllStages_20261026.zip'
sha256sum WorkBuddy_AllStages_20261026.zip
python archive/workbuddy-fourline-2026-10-26/tools/verify_package.py \
  --zip WorkBuddy_AllStages_20261026.zip
```

## What is *not* in the release

- No `.venvs`, `node_modules`, `.git` object database, or other runtime cache from
  `E:\WorkBuddyProject`. These total roughly 7.9 GB of the 10.07 GB local tree and are
  reproducible from lockfiles; they are not evidence.
- No `data/` root and no `D008`/`D009`, confirmatory, holdout, sealed or frozen subtree.
  See `EXCLUSION_REPORT.md` §4.
- No credentials. None were detected; the scan is heuristic and that limit is stated.

## If the asset ever needs re-issuing

Do **not** replace this asset in place. Replacing it breaks every downstream hash
reference. Instead:

1. Build a new package under a new name and a new release tag.
2. Record the new outer SHA-256 and a diff against this manifest, naming exactly which
   files changed and why.
3. Keep this release published so old citations remain resolvable.
4. Note the supersession in `README.md` with both digests side by side.

The same rule applies to `/docs/archive/` inside the package: a superseded version is
kept, never overwritten. Several superseded protocol revisions (`science_v9/
genesis_feasibility_v3r3..v3r14`, `science_v7/anti_q4h_d7r1..r3`) are preserved for
exactly this reason.