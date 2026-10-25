# Finishing the original WorkBuddy asset transfer

Target: https://github.com/lyxxx708/hessian-landscape (public)

Current stage: **report uploaded only**. Source folder mentioned in the report: `E:\WorkBuddyProject` on user's Windows host (not mounted in this environment). Work from a review branch, not a destructive rewrite of `main`.

## 1. Locate authoritative package

On the authorized Windows machine, use PowerShell to locate the original prepared ZIP and associated manifest/verification records. Do not search inside frozen, private or holdout subtrees when outside scope.

```powershell
$Root = 'E:\WorkBuddyProject'
Get-ChildItem -LiteralPath $Root -Recurse -File -Include *.zip,MANIFEST.csv,MANIFEST.sha256,PACKAGE_VERIFICATION.json |
  Select-Object FullName,Length,LastWriteTime |
  Sort-Object FullName
```

The report does not provide a reliable source ZIP filename; do **not** invent it.

## 2. Validate identity / integrity

Review `MANIFEST.csv` schema and path roots before trusting it. Verify file sizes and SHA-256 for every included source byte and confirm `MANIFEST.sha256` really matches the manifest. Compare `PACKAGE_VERIFICATION.json` with an independent streaming verification of the ZIP entries. Inspect the package ZIP central directory for path traversal, duplicates, unexpected external links and missing/extra files.

Example outer-package check:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'X:\actual\source-archive.zip'
```

`X:\actual\...` is deliberately a placeholder; replace it with the **observed** source location.

## 3. Perform public-release exclusion checks

**Stop** and do not publish if the package contains any account/token/password/credential material, private Bridge database, personal identifying information, unauthorized third-party content, private frozen NAO D008/D009, holdout data, or original `.git` database. Report all exclusions. Do not blindly trust the report's assertion about exclusions.

## 4. Choose the large-file transport

The report says the *underlying original files* total 2,139,736,566 bytes; it does **not** specify final ZIP size. Ordinary GitHub Git objects are unsuitable for that scale (100 MiB per normal file upper bound). Evaluate **Git LFS** limits/quota for the actual account, or create a **GitHub Release** with separately hashed parts when authenticated release upload is available. A Release URL without uploaded bytes, a Git LFS pointer without accessible LFS objects, or a single README is **not** a complete backup.

For Git LFS, only after source review and LFS capability check:

```powershell
git lfs install
git lfs track 'archive/workbuddy-fourline-2026-10-26/payload/*'
git add .gitattributes
```

Split into appropriately sized immutable parts **only if necessary**, and record SHA-256 and byte size of each part plus full reconstructed package digest. Never rename parts without updating the manifest.

## 5. Review branch and remote verification

1. Commit metadata and a package index separate from archive bytes.
2. Upload approved package parts to the selected transport.
3. Inspect the remote Git ref, artifact links and reported object sizes.
4. Retrieve/download the entire uploaded package through a separate path.
5. Compare its SHA-256 with the source and verify every original `MANIFEST.csv` entry.
6. Only then update `README.md` from `PARTIAL` to `FULL_ARCHIVE_VERIFIED`.
7. Merge to `main` after review; preserve the existing GENESIS-only documentary history.

## 6. Scientific and operational limits

Archiving does not approve any new scientific run, change frozen gates, repair historic failures, or establish fresh replication. Preserve old `FAIL`, `STOP`, `REVISE` and `SOURCE_MISSING` outcomes. The first verified upload should be a **data custody milestone**, not a scientific discovery claim.
