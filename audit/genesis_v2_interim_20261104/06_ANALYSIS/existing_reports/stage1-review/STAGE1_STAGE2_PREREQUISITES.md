# Stage 1–2 prerequisite audit (2026-11-02)

Source: `E:\GENESIS\worktrees\genesis-v2`, HEAD `6693dde3f0049620b4250b4982f1c6ef43cbefa3`. No source changes.

Verified: manifest 143/143 files matches after CRLF-to-LF normalization; E: ~3.66 TB free; RTX 4070 Ti 12GB detected; no active GENESIS GPU worker. `py -0p` exposes 3.12 and 3.10 only, with a third-party old 3.11 runtime under C: which the E-first contract does not permit as the reproducible toolchain. Bootstrap hardcodes `py -3.11` and has no explicit interpreter path parameter. Therefore bootstrap and software tests remain unrun.

Old regression evidence: clean upstream branch's `tests/` has only `test_reference_block_metrics.py` (1,132 bytes); `repo2` likewise has a single test file and unrelated local history/a loose file. `repo` is an incomplete no-commit archive with many staged additions and no `AGENTS.md` or v2 source. No intact legacy regression baseline identified; did not apply overlay or test against a fabricated baseline.

Data consent: no independent per-source rights review/acceptance receipt interface exists in current CLI. First launch's single `--accept-licenses` sets `text_license_accepted=True` and `image_license_accepted=True` and downloads MNIST, CIFAR-10 and Project Gutenberg eBook 100 as a batch. `study_v2.yaml` currently marks both false and text hash null. No license/source/hash/terms review was performed, and this audit did not invoke prepare-data or accept the bulk license flag. Further review of the exact dataset provider terms and frozen source hashes is required before downloading.

No environment installation, network dataset request, G0 or study run was performed. See parent `INCOMPLETE_BLOCKED_EVIDENCE.md` for primary recovery command and GPU/disk receipt.
