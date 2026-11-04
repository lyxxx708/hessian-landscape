# INCOMPLETE_BLOCKED_EVIDENCE — GENESIS v2 local qualification

Updated: 2026-11-02 (Asia/Singapore). Source branch HEAD: `6693dde3f0049620b4250b4982f1c6ef43cbefa3`; isolated branch `codex/genesis-v2-local-run` at `E:\GENESIS\worktrees\genesis-v2`.

## Completed verified gates

- Source DELIVERY_MANIFEST: 143 files match after CRLF-to-LF normalization (Windows checkout line endings explain raw size/hash differences).
- E: available space observed ~3.65 TB; RTX 4070 Ti detected, 12,282 MiB; CUDA 12.8 works with Python 3.11.14 / PyTorch 2.10.0+cu128 / torchvision 0.25.0+cu128.
- v2 tests: 80 passed, 1 skipped (Windows directory symlink creation unavailable to unprivileged account); output `stage1-review/v2-tests-final.txt`.
- doctor: ENV_READY, zero errors; CUDA/science qualification still NOT_RUN; `stage1-review/doctor.txt`.
- Legacy main baseline was overlaid in a separate E: worktree without replacing historical files; unittest and pytest each 17 passed; `legacy-unittest.txt`, `legacy-pytest.txt`.
- Driver plan dry-runs only: S1 130 training runs; S2 96; `plan-s1.txt`, `plan-s2.txt`.

## Current hard block: Stage 3 data rights/source identity (DATA_BLOCKED)

- Configured Gutenberg #100 is not established as an unrestricted public-domain corpus: the eBook page itself says this digital edition is copyrighted 1990–1993 by World Library, calls it not public domain, and limits copying/distribution to personal noncommercial use. The config calls it public domain and has no expected source SHA. Source: https://www.gutenberg.org/ebooks/100 (also `pg100.html` in the Gutenberg cache).
- Gutenberg's general license directs non-US users to check local law. This run has not established Singapore copyright/use status for this protected digital edition: https://www.gutenberg.org/policy/license.html.
- CIFAR-10 official distribution page gives dataset facts, citation request, download versions and MD5, but the inspected page does not state a license: https://www.cs.toronto.edu/~kriz/cifar.html.
- MNIST original source page could not be fetched; reusable rights/terms remain unverified. Third-party mirrors were not used to infer broadened rights: https://yann.lecun.com/exdb/mnist/.
- No datasets downloaded. `text_license_accepted` and `image_license_accepted` remain false. No G0, protocol freeze, S1/S2, or S3 started.
- Stage 3 audit and dry-run evidence: `stage1-review/DATA_RIGHTS_AUDIT.md`, `plan-s1.txt`, `plan-s2.txt`.

## Recovery

Obtain permitted exact sources and immutable SHA256/version records for each configured real dataset. For Shakespeare, resolve the mismatch between the configured Gutenberg #100 digital edition and its included copyright notice, or approve a documented source/protocol correction before outcomes. For CIFAR-10 and MNIST, establish rights from original rights holders/providers. Do not toggle acceptance flags or use the batch `--accept-licenses` until each source passes. After any protocol/source correction, rerun full manifest and software tests, data hashing/split receipt, G0, and freeze before S1.

Commands after rights are established (run from `E:\GENESIS\worktrees\genesis-v2\implementation\genesis-v2` in the E:-configured process environment):

```powershell
$Py = 'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe'
& $Py -m genesis_gpu --config configs\study_v2.yaml --root E:\GENESIS\runs\genesis_full_v2 prepare-data --accept-licenses
& $Py -m genesis_gpu --config configs\study_v2.yaml --root E:\GENESIS\runs\genesis_full_v2 doctor
& $Py -m genesis_gpu --config configs\study_v2.yaml --root E:\GENESIS\runs\genesis_full_v2 g0 --all --save-reference
```

Do not launch S1 until Stage 4 numerical G0 and Stage 5 protocol freeze pass.
