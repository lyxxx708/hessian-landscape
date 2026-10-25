# Integrity report — WorkBuddy four-line archive, 2026-10-26

**Claimed integrity level: `FULL_ARCHIVE_VERIFIED`** — all 63 released chunks re-downloaded through the public URL, each chunk's server-declared and locally recomputed SHA-256 matched, reassembly reproduced the 2,089,046,079-byte package digest, and every one of the 2,024 content members re-verified against the manifest carried inside the download.

Every number below was produced by an executed command against the actual bytes on the
authoritative local disk. Nothing in this file is transcribed from the 2026-10-26 report.

## 1. What was found

The 2.14 GB payload **was** located. The earlier branch documentation stated it was
"not present here"; that statement was true for the environment that wrote it (a ChatGPT
mount with no access to `E:\WorkBuddyProject`), and it is now superseded by observation.

| Item | Observed value |
| --- | --- |
| Original package | `WorkBuddy_AllStages_20261026.zip` |
| Package location | `C:\Users\lyxxx\Documents\Codex\2026-10-21\referenced-chatgpt-conversation-this-is-an\outputs\` |
| Package bytes | **2,089,046,079** |
| Package SHA-256 | `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` |
| Companion manifest dir | `...\outputs\WorkBuddy_AllStages_20261026\` |
| `MANIFEST.csv` bytes | 325,349 |
| `MANIFEST.csv` SHA-256 | `f24b79119d5fb96c59ab4afc76420cdc9734fa84a8e2a21b89455edf41401836` |
| `MANIFEST.sha256` bytes | 80 on disk / 79 inside the package (newline normalised — see §3) |
| Verification record | `WorkBuddy_AllStages_20261026_VERIFICATION.json`, 1,223 bytes, `status: PASS` |
| Source project root | `E:\WorkBuddyProject` — 33,442 files / 10,067,570,810 bytes |

The package was **not** in `E:\WorkBuddyProject`. It lives one level above the report
outputs used to build it. Searching only the declared source root would have produced a
false "archive missing" conclusion — which is exactly what the previous session
concluded.

## 2. Package identity

Streaming SHA-256 over 2,089,046,079 bytes in 8 MiB chunks (constant memory):

```
observed  290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f
recorded  290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f
MATCH     True
```

## 3. Manifest binding

`MANIFEST.sha256` contains exactly one line, binding the manifest itself:

```
f24b79119d5fb96c59ab4afc76420cdc9734fa84a8e2a21b89455edf41401836  MANIFEST.csv
```

Independently recomputed over `MANIFEST.csv` → identical digest. The binding holds.

### One byte of difference between disk and package, and why it is harmless

`MANIFEST.sha256` is **80 bytes on disk** (CRLF line ending) but **79 bytes inside the
package** (LF). The packaging step normalised the newline of that one sidecar. Recording
it because a reader comparing the two sizes would otherwise suspect a truncated file:

| Object | Bytes | SHA-256 |
| --- | --- | --- |
| `MANIFEST.sha256` on disk | 80 | `43cd5de17247f5769d63c47f8358e69bf9dd698d6e78d9912cb037ef7354b222` |
| `MANIFEST.sha256` in package | 79 | `809c5686ffd8fc6b6636f54366763897d5d82b2906d8df68b2f9caefd5caa06a` |

The two are byte-identical after CRLF→LF normalisation, and the difference is confined to
the trailing newline of a single line. Critically, **`MANIFEST.csv` is byte-identical in
both places** — 325,349 bytes, SHA-256 `f24b7911…01836` — so the object the digest
actually binds is unchanged and the binding is still verifiable. A sidecar whose own
line ending shifted does not affect any member digest, because member digests are computed
over decompressed member content, not over the sidecar.

## 4. Per-entry verification of every package member

Each of the 2,024 content members was decompressed and re-hashed with an independent
SHA-256 (CRC is also enforced by the decompressor). Sizes were compared against both the
central directory and the manifest.

| Check | Result |
| --- | --- |
| Members in central directory | 2,026 |
| Content members verified | 2,024 |
| Sidecars (manifest + binding) | 2 |
| Manifest entries | 2,024 |
| Uncompressed content bytes re-read | 2,141,079,119 |
| Size mismatches | **0** |
| SHA-256 mismatches | **0** |
| Manifest entries absent from package | **0** |
| Package members absent from manifest | **0** |
| Read / CRC errors | **0** |

Independent equality: `2,024 content + 2 sidecars = 2,026 members`, and
`2,024 content members = 2,024 manifest entries` with zero set difference in either
direction. The package neither invents nor drops a file.

## 5. Structural safety of the package

| Attack surface | Result |
| --- | --- |
| Path traversal (`..` segments) | 0 |
| Absolute paths (`/…`, `X:\…`) | 0 |
| Duplicate member paths | 0 |
| Symlink / special-mode entries | 0 |
| Damaged entries | 0 |

## 6. Declared-scope reconciliation

The package declares its scope in `COLLECTION_SCOPE.json`: 1,984 project files /
2,139,736,566 bytes across 50 named roots. Reconciling that declaration against the
actual manifest:

| Quantity | Value |
| --- | --- |
| `COLLECTION_SCOPE.json` declared | 1,984 files / 2,139,736,566 bytes |
| Manifest rows matching a declared root | 1,949 files / 2,139,627,497 bytes |
| Declared roots with exact file+byte match | 49 / 50 |
| Unmatched rows | 48 files / 961,308 bytes |
| Total project rows | 1,997 files / 2,140,588,805 bytes |

The single "drift" is not a loss. The 48 unmatched rows decompose exactly:

- 30 top-level governance files (`PROJECT_CHARTER.md`, `RESEARCH_PROTOCOL.md`,
  `BOOTSTRAP_SHA256.csv`, all `START_*.ps1`/`.cmd`, …) plus 5 `config/*.json`
  = **35 files / 109,069 bytes**, which is byte-for-byte the declared `root_governance`
  bucket. The scope file names that bucket synthetically rather than listing paths, so
  prefix matching cannot see it. This explains the entire apparent drift.
- 7 `conversation_reports/*` files — 143,531 bytes
- 6 `packaging_tools/*` files — 708,708 bytes

Arithmetic closes exactly: `1,984 + 13 = 1,997` files, and
`2,139,736,566 + 143,531 + 708,708 = 2,140,588,805` bytes. **No declared file is missing
from the package.** The 13 extra rows are packaging provenance — the inventory/rendering
tools and the conversation records they drew on — retained deliberately as the audit
trail for how the report was produced.

## 7. Report-cited sources resolve

`SOURCE_INDEX.tsv` cites 19 report-critical originals (S01–S19). All **19 / 19** resolve
to an exact package member, with byte sizes taken from the manifest, not from the index.
Zero unresolved. The report's citation chain is therefore intact inside the package — a
claim the previous revision could not make, because it had none of these files.

## 8. How `FULL_ARCHIVE_VERIFIED` was reached

This level was withheld until the uploaded bytes had actually been fetched back through a
path independent of the uploader, and granted only after all five gates passed. The ladder
is recorded because "verified" without it is an assertion rather than evidence.

| Gate | Test | Result |
| --- | --- | --- |
| V1 `ASSET_PRESENT` | all 63 names exist on the release, `state: uploaded`, and the server-declared digest equals the manifest digest | **PASS** |
| V2 `ASSET_DOWNLOADABLE` | a real HTTPS GET of each asset returns 200 and the transferred byte count equals the manifest `bytes` | **PASS** |
| V3 `CHUNK_HASH` | SHA-256 recomputed over each *downloaded* chunk equals the manifest digest — computed locally, not read from the API | **PASS** |
| V4 `REASSEMBLY` | the 63 chunks concatenated in manifest order give 2,089,046,079 bytes and `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f` | **PASS** |
| V5 `INNER_PACKAGE` | all 2,024 members of the reassembled zip re-hash to their `MANIFEST.csv` values, streamed member by member | **PASS** |

V1 and V2 are separate on purpose: an asset can be *listed* by the API while its download
URL 404s — that is exactly what a `starter` record does — so presence alone proves nothing
about retrievability.

V3 is the gate that carries the most weight. It is computed over bytes that arrived across
the network during this check, so a chunk corrupted anywhere between the original disk and
the CDN cannot pass. V4 then proves the *set and order* are right, not merely that each
piece is individually intact: a perfectly valid chunk sitting in the wrong position passes
V3 and fails V4. V5 closes the loop by re-deriving the package's own internal manifest from
the downloaded artifact, so the claim depends on no file produced before the upload.

The reassembled digest was additionally recomputed by an unrelated one-off script and
matched again, so this does not rest on one program agreeing with itself. Finally the live
release was reconciled against `CHUNK_MANIFEST.csv` in both directions — 63 assets, 63
manifest rows, 0 mismatches, 0 extra assets, verdict `RELEASE_MATCHES_MANIFEST`.

Two honest limits survive this verification:

1. **Scope boundary, not completeness.** The package covers the 50 declared roots plus
   packaging provenance. `E:\WorkBuddyProject` holds another ~7.9 GB (`.venvs`,
   `node_modules`, `.git`, other session trees) that the packaging scope excluded as
   runtime/dependency cache. That exclusion is intended and declared, not a gap.
2. **Content scan is heuristic.** The credential scan matches known key shapes over
   decoded text. It cannot prove the absence of an arbitrarily encoded secret. Reported as
   a heuristic, never as a guarantee.

What `FULL_ARCHIVE_VERIFIED` does **not** mean: it does not certify the scientific claims
inside the package, and it does not assert that the archive captures all work ever done. It
asserts that the published artifact reproduces the verified source package, member for
member, through a path independent of the process that produced it.

## 9. Reproduce this report

```bash
python tools/verify_package.py --zip WorkBuddy_AllStages_20261026.zip
```

The bundled verifier recomputes the outer hash, the manifest binding, and every
per-entry digest, then prints the same table. Expected totals: 2,026 members,
2,024 content, 2,141,079,119 content bytes, 0 mismatches.

The verifier was itself negatively tested — it is not a test that always passes:

| Injected fault | Observed |
| --- | --- |
| Package truncated to 4,096 bytes | `outer bytes MISMATCH`, `outer sha256 MISMATCH`, `FAIL not a valid zip` |
| One hex digit flipped in one manifest digest (external manifest, 2,024 entries) | `hash mismatch 1 FAIL`, `RESULT PACKAGE_FAILED` |

Both faults were caught. A single-character corruption anywhere in the manifest is
sufficient to fail the run.