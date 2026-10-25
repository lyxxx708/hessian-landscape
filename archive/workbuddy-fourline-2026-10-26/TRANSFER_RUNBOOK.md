# Transfer runbook — SUPERSEDED, retained as history

> **Status: `SUPERSEDED_VERSION`. Do not follow this procedure.**
>
> This file described how to *find and upload* the missing payload. That work has been
> done. It is kept unedited below because it is the record of the incomplete earlier state:
> the previous session could not see `E:\WorkBuddyProject` and wrote a correct plan for an
> operator who could.
>
> Current procedure: [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md).
> Current evidence: [INTEGRITY_REPORT.md](INTEGRITY_REPORT.md),
> [EXCLUSION_REPORT.md](EXCLUSION_REPORT.md), [RELEASE_ASSETS.md](RELEASE_ASSETS.md).

## What this runbook got right

It correctly insisted that a Release URL without uploaded bytes, or an LFS pointer without
accessible objects, does not constitute a backup. It correctly refused to invent the
package filename or size. It correctly demanded re-download verification before changing
the status label. Those constraints were honoured.

## Where it was wrong, and why it mattered

| Its assumption | What was actually true |
| --- | --- |
| Search for the ZIP under `E:\WorkBuddyProject` | The ZIP is **outside** the project root, in `...\Documents\Codex\2026-10-21\referenced-chatgpt-conversation-this-is-an\outputs\`. Following the runbook literally would have produced a false "archive missing" verdict. |
| `PACKAGE_VERIFICATION.json` was the expected filename | The file on disk is `WorkBuddy_AllStages_20261026_VERIFICATION.json`. |
| The outer ZIP size was unknown | It is 2,089,046,079 bytes and was recorded in `_SHA256.txt` all along. |
| Evaluate LFS as the likely transport | LFS is enabled but the free tier is 1 GiB storage / 1 GiB egress — unusable for a 2.089 GB package. A Release asset was the viable route. |
| `MANIFEST.csv` and `MANIFEST.sha256` were "not uploaded here" | They exist inside the ZIP as members and outside it as sidecars; both were verified. |

The transferable lesson: **"not found in the expected place" is not "not present".** The
package had to be located by searching the parent of the report-outputs tree, not the
declared source root.

---

## Original text, unedited

Target: https://github.com/lyxxx708/hessian-landscape (public)

Current stage: **report uploaded only**. Source folder mentioned in the report: `E:\WorkBuddyProject` on user's Windows host (not mounted in this environment). Work from a review branch, not a destructive rewrite of `main`.

### 1. Locate authoritative package

On the authorized Windows machine, use PowerShell to locate the original prepared ZIP and associated manifest/verification records. Do not search inside frozen, private or holdout subtrees when outside scope.

```powershell
$Root = 'E:\WorkBuddyProject'
Get-ChildItem -LiteralPath $Root -Recurse -File -Include *.zip,MANIFEST.csv,MANIFEST.sha256,PACKAGE_VERIFICATION.json |
  Select-Object FullName,Length,LastWriteTime |
  Sort-Object FullName
```

The report does not provide a reliable source ZIP filename; do **not** invent it.

### 2. Validate identity / integrity

Review `MANIFEST.csv` schema and path roots before trusting it. Verify file sizes and SHA-256 for every included source byte and confirm `MANIFEST.sha256` really matches the manifest. Compare `PACKAGE_VERIFICATION.json` with an independent streaming verification of the ZIP entries. Inspect the package ZIP central directory for path traversal, duplicates, unexpected external links and missing/extra files.

Example outer-package check:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'X:\actual\source-archive.zip'
```

`X:\actual\...` is deliberately a placeholder; replace it with the **observed** source location.

### 3. Perform public-release exclusion checks

**Stop** and do not publish if the package contains any account/token/password/credential material, private Bridge database, personal identifying information, unauthorized third-party content, private frozen NAO D008/D009, holdout data, or original `.git` database. Report all exclusions. Do not blindly trust the report's assertion about exclusions.

### 4. Choose the large-file transport

The report says the *underlying original files* total 2,139,736,566 bytes; it does **not** specify final ZIP size. Ordinary GitHub Git objects are unsuitable for that scale (100 MiB per normal file upper bound). Evaluate **Git LFS** limits/quota for the actual account, or create a **GitHub Release** with separately hashed parts when authenticated release upload is available. A Release URL without uploaded bytes, a Git LFS pointer without accessible LFS objects, or a single README is **not** a complete backup.

Split into appropriately sized immutable parts **only if necessary**, and record SHA-256 and byte size of each part plus full reconstructed package digest. Never rename parts without updating the manifest.

### 5. Review branch and remote verification

1. Commit metadata and a package index separate from archive bytes.
2. Upload approved package parts to the selected transport.
3. Inspect the remote Git ref, artifact links and reported object sizes.
4. Retrieve/download the entire uploaded package through a separate path.
5. Compare its SHA-256 with the source and verify every original `MANIFEST.csv` entry.
6. Only then update `README.md` from `PARTIAL` to `FULL_ARCHIVE_VERIFIED`.
7. Merge to `main` after review; preserve the existing GENESIS-only documentary history.

### 6. Scientific and operational limits

Archiving does not approve any new scientific run, change frozen gates, repair historic failures, or establish fresh replication. Preserve old `FAIL`, `STOP`, `REVISE` and `SOURCE_MISSING` outcomes. The first verified upload should be a **data custody milestone**, not a scientific discovery claim.