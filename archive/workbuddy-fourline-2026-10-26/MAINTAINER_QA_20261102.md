# Maintainer QA and evidence scope — 2026-11-02

**Integration decision: archive provenance and download instructions, not independent scientific replication.**

## What was verified in this review

- GitHub Release `archive-20261026` is publicly listed with **63 uploaded assets** whose API-reported sizes sum to **2,089,046,079 bytes**.
- The branch contains a standalone standard-library package verifier with a fixed expected outer SHA-256 (`290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f`), manifest hash checks, streaming member hashes, no extraction calls, and documented negative controls.
- The branch's `EXPERIMENT_REPORT.md` blob SHA is identical to the already integrated **canonical** report at `research/workbuddy/2026-10-26/EXPERIMENT_REPORT.md`: `9d6ce23fd3fdb04c2fef3c105b722a363ec13ab4`. The latter remains authoritative for status and citations; the archive-path duplicate is an unchanged snapshot, not a competing source of truth.
- GitHub Actions unit tests passed on the PR head prior to this additive note.

## Boundaries

- The author's `INTEGRITY_REPORT.md` records a previous complete 63-chunk re-download, package reassembly, and 2,024-member digest validation. **This maintainer session did not independently download/re-hash 2.09 GB**; it corroborated the live GitHub asset count/sizes, source verifier, and report consistency.
- Hash integrity of a supplied archive **does not verify scientific claims**, validate old experiments, recover the missing 2025 Phase IV/V Hessian checkpoint, or certify inclusion of all private local research files.
- `EXCLUSION_REPORT.md` documents a heuristic publication scan and a minor local username path disclosure. It is the author-side scan, not a guarantee that no secret or restricted third-party material exists.
- The GitHub Release assets were already public before this merge. The PR adds documentary metadata and a verifier to Git; it does not newly upload raw research bytes to Git source history.
- Do not mark historical experiments `FRESH_PASS` based only on archive integrity or this PR.

**Current evidence classification:** `PUBLIC_ARCHIVE_LOCATED; RELEASE_METADATA_CHECKED; AUTHOR-REPORTED_FULL_ARCHIVE_VERIFIED; SCIENTIFIC_REPLICATION_NOT_ESTABLISHED`.
