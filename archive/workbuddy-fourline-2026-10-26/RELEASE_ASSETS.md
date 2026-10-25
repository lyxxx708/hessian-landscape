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

## Transport was split, because the uplink is the binding constraint

The package fits inside GitHub's 2 GiB per-asset limit, so at first pass this file said
"there are no split parts". **That turned out to be wrong in practice and is corrected
here**, because the plan that survives contact with a slow link is not the plan you write
when you only check server-side limits.

Measured facts that forced the change:

| Measurement | Result |
| --- | --- |
| Upload to `uploads.github.com` (proxied) | 108,402 B/s over a 50 MB probe |
| Upload to `uploads.github.com` (direct, no proxy) | 126,956 B/s over a 20 MB probe |
| Upload to `httpbin.org` (independent of GitHub) | **126,432 B/s ≈ 1.0 Mbit/s** |
| Observed during the real part-01 transfer | **85,100 B/s** |
| Four concurrent 10 MB uploads | No aggregate gain — bandwidth does not stack |

The independent reference point matters: because a non-GitHub host reports the same
~126 KB/s, the slowness is **not GitHub-specific throttling**. What was *not* separately
isolated is whether the bottleneck is the local uplink, the international hop, or the
local proxy — all three sit on the same path between this host and `httpbin.org`, so this
measurement cannot distinguish them. Stated as measured rather than as inferred.

Whatever the cause, it is a property of the path this archive was built over, and it sets
the wall-clock floor: 2,089,046,079 bytes at 85–126 KB/s is **4.6–6.8 hours** of
continuous transmission. A faster path would shorten that; the plan below is what makes
the transfer survivable on this one.

A single 4.6-hour uninterrupted POST is a bad bet on a link that has already produced
intermittent empty responses, because one dropped connection discards the whole 2 GB.
So the package is transmitted as **five independent parts**, each of which is separately
resumable and separately verifiable:

| Part | Bytes | Offset | SHA-256 |
| --- | --- | --- | --- |
| `...zip.part01` | 419,430,400 | 0 | `526481f1a407131c4921d1e1617b5760ff60452d083e9a182fc9d5386c2c8fdd` |
| `...zip.part02` | 419,430,400 | 419,430,400 | `076f1a75197ba17b0c47f5d6d3bad6d4c370e700715c4135fc08872301e302e2` |
| `...zip.part03` | 419,430,400 | 838,860,800 | `b74ad5e227e300880b0efcfb9904f8841e54e71d66cfdea16df5f5f8afe4b5ad` |
| `...zip.part04` | 419,430,400 | 1,258,291,200 | `62ccb4a0df36fd779b28170c93e78f402638e9f30003fb933923dbfde1a9b3bc` |
| `...zip.part05` | 411,324,479 | 1,677,721,600 | `ac4b71a0641f87a41ab0f22c987c2066bb603f39386bf57ffe33f7925ed71313` |

Concatenating the five parts in order reproduces the original package exactly — the
reassembled digest was computed and equals
`290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f`. `REPRODUCTION_GUIDE.md`
gives the reassembly-and-check sequence. Parts are named so that a plain lexicographic
sort puts them in the correct order.

### Re-compressing to cut transfer volume was tested and rejected

On a 4.6-hour transfer the obvious optimisation is to send fewer bytes. It does not work
here, and the measurement is recorded so nobody re-litigates it:

| Member | Uncompressed | Stored in package | Ratio |
| --- | --- | --- | --- |
| `anti_slowing/bundle/raw.npz` | 1,872,383,078 | 1,870,874,515 | **0.999** |
| `nao_v3/bundle/raw.npz` | 181,428,436 | 178,842,364 | 0.986 |
| `signed_sokal/bundle/raw.npz` | 10,899,768 | 10,898,855 | 1.000 |
| `welch_spectrum.json` | 21,114,525 | 4,559,634 | 0.216 |
| All 14 `.npz` | 2,080,661,986 | 2,076,081,517 | 0.998 |

98% of the payload is float64 numerical arrays that are already incompressible — deflate
recovers 1.5 MB out of 1.87 GB on the largest one. Only the one JSON spectrum compresses
meaningfully (0.216), and at 21 MB it is 1% of the total. Recompressing would therefore
change the digest to buy roughly **15 MB**, i.e. about two minutes out of 4.6 hours, at
the cost of destroying byte-exact identity with the original package and its 2026-10-25
verification record. Rejected.

## The asset

The package identity is fixed regardless of how it travels. These are the numbers that
identify the *content*, and they are what any downstream citation should quote.

| Field | Value |
| --- | --- |
| Original package name | `WorkBuddy_AllStages_20261026.zip` |
| Release tag | `archive-20261026` |
| Release URL | https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026 |
| Bytes | **2,089,046,079** |
| SHA-256 | `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` |
| Content | 2,026 members — 2,024 content + `MANIFEST.csv` + `MANIFEST.sha256` |
| Uncompressed bytes, 2,024 content members | 2,141,079,119 |
| Uncompressed bytes, both sidecars | 325,428 (`MANIFEST.csv` 325,349 + `MANIFEST.sha256` 79) |
| Uncompressed bytes, all 2,026 members | 2,141,404,547 |

The two uncompressed totals differ by exactly the sidecar bytes; earlier drafts quoted
only the content figure, so the accounting is spelled out here rather than left to be
misread as a discrepancy.

### Which asset you actually download

The release carries the five `part0N` assets, **not** a single monolithic zip. This is
recorded plainly because a reader who follows only the transport table above would expect
one file and find five. Section "Verification record" below states what has been proven
about the uploaded bytes and what has not.

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

Two different things can be "verified", and conflating them is how archives acquire
false confidence. Kept separate on purpose:

**1. The local package is internally closed.** All 2,024 content members were streamed
and hashed and matched against `MANIFEST.csv`: zero mismatches. Member CRCs checked, no
path traversal, no absolute paths, no duplicate members, no symlinks. This is a strong
result and it is about the *source*.

**2. Whether the uploaded bytes are correct.** This requires downloading them back and
hashing them, which is a separate claim. `INTEGRITY_REPORT.md` records the outcome and
`README.md` states the current integrity level; read those rather than inferring a
completed round trip from this file's presence.

The command that produces the authoritative answer, runnable by anyone:

```bash
gh release download archive-20261026 --repo lyxxx708/hessian-landscape
cat WorkBuddy_AllStages_20261026.zip.part0* > WorkBuddy_AllStages_20261026.zip
python archive/workbuddy-fourline-2026-10-26/tools/verify_package.py \
  --zip WorkBuddy_AllStages_20261026.zip
```

`verify_package.py` recomputes the outer SHA-256, checks the member count, and re-checks
every member against the manifest — so a single flipped byte in any of the five parts
surfaces as a failure rather than as a plausible-looking archive.

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