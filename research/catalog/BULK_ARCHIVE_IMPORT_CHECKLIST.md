# Bulk original archive receipt — NOT YET COMPLETED

The WorkBuddy 2026-10-26 report describes `1,984 files / 2,139,736,566 bytes`. This GitHub research repository currently stores a documentary subset. The full package, figures, raw arrays and immutable run receipts **were not accessible to the GitHub-documentation import**.

When actual archives can be accessed:

1. **Quarantine and inspect:** retrieve using an authenticated channel; never execute imported scripts, deserialize untrusted pickle files or follow manifest paths outside the archive root. Scan for secrets, personal information, copyrighted/licensed data and holdouts before publishing to this public repo.
2. **Bind identity:** compute outer archive SHA256, size, filename and generator details; compare against an already-existing independent receipt (not a newly invented expected hash).
3. **Verify every member:** extract to a clean scratch path, prevent zip-slip/absolute paths and symlink escapes; compare count, sizes, SHA256, source paths against the archive's actual `MANIFEST.csv` and `MANIFEST.sha256`.
4. **Preserve distinctions:** retain raw producer status, failed jobs, stderr, post-failure forensic recomputation, revisions and negative results as separate artifacts. Keep prior `SUPERSEDED` / `FAIL` labels readable rather than silently deleting or replacing them.
5. **Upload strategy:** do not directly commit the ~2.14 GB package to ordinary Git objects. Split into versioned, checksummed, publication-approved shards or store in a suitable versioned artifact location, linking immutable hashes from this repo. GitHub limits, quotas and LFS policies must be checked for the actual hosting plan.
6. **Promote only after verification:** update receipt table with source SHA256, size, path/URI, validation operator, validation log and date; if incomplete mark `MISSING_OR_UNVERIFIED`. A GitHub pull request merge is not scientific authorization.

## Receipt table

| Asset | Expected from report | Actual SHA256 / bytes | Current status |
| --- | --- | --- | --- |
| WorkBuddy ZIP | Includes 1,984 project files, 2,139,736,566 uncompressed source bytes | Not independently observed | MISSING_OR_UNVERIFIED |
| MANIFEST.csv | Member SHA256 and byte counts | Not observed | MISSING_OR_UNVERIFIED |
| MANIFEST.sha256 | Hash binding for manifest | Not observed | MISSING_OR_UNVERIFIED |
| PACKAGE_VERIFICATION.json | Streamed ZIP verification report | Not observed | MISSING_OR_UNVERIFIED |
| Source figures and run receipts | `figures/`, `project/records/` referenced in report | Not observed | MISSING_OR_UNVERIFIED |

This file is a tracking tool, not a claim that a package was verified.
