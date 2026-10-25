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
| Observed during the real part-01 transfer | **85,100 B/s** steady state |
| Download from `github.com`, same proxy | **1,553 KB/s ≈ 12.7 Mbit/s** |
| **Parallel uploads, short-burst probe** | 2 streams 182 KB/s · 4 → 331 · 8 → 574 · 16 → **762 KB/s** |
| **The run that completed all 63 chunks** | **3–4 streams, ~492 KB/s aggregate, 134 KB/s median per stream** |

The last two rows are not the same quantity and must not be quoted interchangeably. The
probe measures a short burst at a given concurrency; the final row is what 2.089 GB actually
sustained over 69 minutes. The probe's high-concurrency arms also failed intermittently —
at 16 streams, 14 chunks returned `HTTP 404` after transferring their full 32 MiB — so 762
KB/s was not reachable for a long transfer on this host. The completing run stayed at 3–4.

The reference point matters: because a non-GitHub host reported the same ~126 KB/s, the
slowness is **not GitHub-specific throttling**.

### It is the upstream direction, not the proxy and not the route

One further measurement settles where the cap lives, and it changes the recommendation:

| Direction | Path | Measured |
| --- | --- | --- |
| **Up** to `uploads.github.com` | via local proxy `127.0.0.1:7897` | 108,402 B/s |
| **Up** to `uploads.github.com` | **direct, proxy bypassed** | 126,956 B/s |
| **Up** to `httpbin.org` | via proxy | 126,432 B/s |
| **Up** during the real transfer | via proxy | 56,000–98,000 B/s |
| **Down** from `github.com` | via the same proxy | **1,553 KB/s (12.7 Mbit/s)** |

Download over the *same* proxy to the *same* host class is roughly **12× faster than
upload**. And bypassing the proxy entirely does not raise upload speed. Together those two
facts rule out the proxy, the chosen node, and GitHub as the cause: the constraint is the
**upstream direction itself** (local link or ISP-side upstream provisioning).

Practical consequence, stated so nobody spends hours on it later: **re-routing cannot fix
this.** Switching proxy nodes, splitting further, or using a different host would not
change the ceiling. Only two things would — a different network with real upstream
bandwidth, or shipping fewer bytes. The second was tested and rejected below. So the plan
is to make a long transfer *survivable* rather than fast.

Two further checks closed the remaining "maybe there is a fast path" question:

| Check | Result |
| --- | --- |
| Upload 2 MiB instead of 400 MB | 116.8 KB/s — **smaller is not faster**, so this is a hard ceiling, not a ramping effect |
| `api.github.com` as an alternative upload endpoint | `HTTP 404` — it does not accept uploads; `uploads.github.com` is the only route |
| DNS for `uploads.github.com` | `198.18.0.17` (Clash fake-ip); no alternate edge to steer to |

So there is one route, and it runs at ~117 KB/s. A single clean 2 MiB POST did land in
`uploaded` state immediately, which confirms the endpoint works; the earlier `starter`
outcome was specific to one very long-lived `gh` transfer, not to the API.

Wall-clock floor at 85–127 KB/s over 2,089,046,079 bytes: **4.6–6.8 hours**. The projected
figure at the measured 117 KB/s ceiling is **4.9 hours**; the observed steady state during
the real run (85–98 KB/s) puts it at the slower end.

### The 400 MiB split was wrong too, and here is the measurement that showed it

Five parts of 400 MiB were built, and part01 was launched. It was **reset after 22m13s
having stored ~133 MB**. That single data point invalidates the whole 5-part plan:

| Attempt | Bytes | Outcome |
| --- | --- | --- |
| probe | 2 MB | `uploaded` |
| probe | 20 MB | `uploaded` |
| probe | 50 MB | `uploaded` |
| another session's part | 70.5 MB | `uploaded` |
| **part01** | 400 MB | **connection reset at 22m13s, ~133 MB stored** |

Everything that finished inside ~10 minutes succeeded; the one that needed ~57 minutes
failed. So the endpoint does not hold a single POST much past ~20 minutes, and a 400 MiB
part at ~117 KB/s **can never complete** — retrying it would burn an hour per attempt to
produce nothing. That is the kind of failure that looks like flaky networking and is
actually a sizing error.

Chunks are therefore sized to finish well inside the window even at single-stream speed:

- **32 MiB per chunk → 63 chunks**, ~4.7 min each single-stream, **4× headroom** under the
  ~20 min limit.
- Concurrency was raised only as far as the endpoint tolerated, and the ceiling was lower
  than the throughput table suggests. A 16-way run failed **14 times with `HTTP 404` after
  transferring the full 32 MiB** — the local proxy's TLS connection pool gave out, so the
  404s were a local resource limit wearing a server error code. The run that actually
  completed all 63 chunks used **3–4 concurrent streams**.
- Measured on that run: **69 minutes end-to-end, ~492 KB/s aggregate**, median **134 KB/s**
  per stream. Stated explicitly because the 762 KB/s figure above is a short-burst probe,
  and quoting it as the achieved rate would overstate the transfer by roughly 1.5×.
- Reassembly is `cat WB4L.p* > WorkBuddy_AllStages_20261026.zip`; verifies to
  `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f`.

Per-chunk digests, byte counts and offsets are in `CHUNK_MANIFEST.csv` alongside this file,
and the machine-readable form is `ARCHIVE_INDEX.json → storage.chunks`.

### A test that measured failure as speed

Recorded because it nearly caused a wrong decision. An earlier concurrency probe reported
"2.47× speedup from parallelism" — but its parallel arm had failed **4/4 with HTTP 404**,
and the figure was computed from wall-clock time without checking that any bytes landed.
Deleted assets and unverified POSTs read as fast uploads.

The corrected probe re-reads the release after every round and only counts an upload when
the asset exists there with the expected size. That is where the 182 / 331 / 574 / 762 KB/s
figures come from — stored bytes, confirmed present. Conclusion unchanged, evidence now
real.

Concatenating the 63 chunks in order reproduces the original package exactly — the
reassembled digest was computed and equals
`290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f`. `REPRODUCTION_GUIDE.md`
gives the reassembly-and-check sequence. Chunks are named with a zero-padded three-digit
suffix so a plain lexicographic sort puts them in the correct order.

### A failed upload leaves a ghost that poisons the retry

Worth recording because it turns a transient error into a permanent one, and it is not
obvious from the API surface.

When a chunk POST dies mid-transfer, GitHub keeps an asset record for that name with
`state: "starter"` — it carries the declared `Content-Length` that the server never
received. That record **holds the name**. Any later upload of the same name then streams
the entire 32 MiB and only *then* returns **HTTP 404**, because the name is already claimed
by the ghost. Each retry therefore costs a full chunk of uplink and fails the same way, so
the archive can never converge while a ghost exists.

Observed directly: 19 ghost records accumulated from interrupted attempts, and every
retry against them burned ~450 s apiece before failing.

The fix is to delete non-`uploaded` records before re-posting the same name:

```
DELETE https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset_id}
```

Note the endpoint. Deleting an asset is **not** nested under the release
(`/releases/{id}/assets/{asset_id}` returns 404); the asset id hangs off the repo. Only
records whose `state != "uploaded"` may be removed — an `uploaded` asset is never deleted.

There is a second, self-inflicted version of the same failure: **two uploaders posting the
same release at once**. Both claim names from the same set, so each one poisons the other's
retries. One process must own the release at a time; the uploader enforces this with a
pidfile, and that liveness probe has to decode `tasklist` output as GBK on a Chinese-locale
Windows install — decoding it as UTF-8 raises and makes the probe answer "not running" for
a live process, silently disabling the lock.

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

The release carries **63 `WB4L.pNNN` chunk assets**, not a single monolithic zip and not
the superseded five `part0N` parts. Recorded plainly because a reader who follows only the
transport table above would expect one file and find 63.

| Scheme | Status |
| --- | --- |
| Single 2.089 GB asset | Superseded — cannot finish inside the endpoint's ~20 min POST window |
| 5 × 400 MiB `part0N` | Superseded — 400 MiB needs ~57 min at ~117 KB/s and was reset at 22m13s having stored ~133 MB; all five parts were deleted from the release |
| **63 × 32 MiB `WB4L.pNNN`** | **Current — all 63 uploaded, re-downloaded and verified** |

## Verification record

Two different things can be "verified", and conflating them is how archives acquire false
confidence. Kept separate on purpose.

**1. The local package is internally closed.** All 2,024 content members were streamed and
hashed and matched against `MANIFEST.csv`: zero mismatches. Member CRCs checked, no path
traversal, no absolute paths, no duplicate members, no symlinks. Strong result, and it is
about the *source*.

**2. The uploaded bytes were downloaded back and hashed.** Actually done, not inferred. All
63 chunks were fetched again from the release by an independent script, re-hashed locally,
concatenated in manifest order, and the result re-verified member by member:

| Gate | What it proves | Result |
| --- | --- | --- |
| V1 `ASSET_PRESENT` | all 63 names exist, `state: uploaded`, server digest == manifest digest | **PASS** |
| V2 `ASSET_DOWNLOADABLE` | real GET returns 200 and byte count matches | **PASS** |
| V3 `CHUNK_HASH` | locally recomputed sha256 of each downloaded chunk == manifest | **PASS** |
| V4 `REASSEMBLY` | concatenation reproduces 2,089,046,079 bytes / `290b8429…7ebf1f` | **PASS** |
| V5 `INNER_PACKAGE` | all 2,024 members of the reassembled zip match `MANIFEST.csv` | **PASS** |

Status **`FULL_ARCHIVE_VERIFIED`** at 2026-10-25T21:32:16Z, then reconciled against the live
release in both directions: 63 assets vs 63 manifest rows, 0 mismatches, 0 extra —
`RELEASE_MATCHES_MANIFEST`. `INTEGRITY_REPORT.md` §8 carries the gate rationale, including
why V4 is not redundant with V3.

This does *not* claim the package's contents are scientifically correct, and it does not
audit the ~7.9 GB of runtime cache deliberately excluded.

The command that reproduces the whole ladder, runnable by anyone:

```bash
gh release download archive-20261026 --repo lyxxx708/hessian-landscape --pattern 'WB4L.p*'
cat WB4L.p* > WorkBuddy_AllStages_20261026.zip
sha256sum WorkBuddy_AllStages_20261026.zip   # 290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f
python archive/workbuddy-fourline-2026-10-26/tools/verify_package.py \
  --zip WorkBuddy_AllStages_20261026.zip
```

`cat WB4L.p*` needs no sorting because the zero-padded three-digit suffix makes
lexicographic order equal to concatenation order — that naming choice is what makes the
naive command safe.

## Byte-exactness

The uploaded file **is** the original package. It was not re-zipped, re-compressed, or
re-packed. Rationale: the package had already been proven internally closed — all 2,024
members match the manifest with zero mismatches — so re-archiving would have produced a
new digest for identical content and destroyed the ability to compare against the
`PACKAGE_VERIFICATION.json` record from 2026-10-25. Preserving the original bytes keeps
two independent verifications pointing at the same object.

`recompressed: false` and `byte_exact_preserved: true` in `ARCHIVE_INDEX.json` record
this.

`verify_package.py` recomputes the outer SHA-256, checks the member count, and re-checks
every member against the manifest — so a single flipped byte in any of the 63 chunks
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

## Measured round-trip result

Produced by an independent re-download (`verify_remote63.py`), not transcribed:

| Field | Measured |
| --- | --- |
| Result | **`FULL_ARCHIVE_VERIFIED`** |
| Chunks re-downloaded | 63 |
| Reassembled bytes | 2,089,046,079 |
| Reassembled SHA-256 | `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` |
| Inner members re-hashed | 2,024 |
| Verified at (UTC) | `2026-10-25T21:32:16Z` |
| Release reconciliation | 63 assets vs 63 manifest rows, 0 mismatch, 0 extra |

Gates, each one a prerequisite of the next:

| Gate | Check | Result |
| --- | --- | --- |
| V1 | assets present, `state=uploaded`, server-declared digest matches | PASS |
| V2 | real GET download, byte count matches | PASS |
| V3 | each chunk's SHA-256 recomputed locally | PASS |
| V4 | reassembly reproduces the package digest | PASS |
| V5 | all 2,024 members re-hashed against the in-package manifest | PASS |
