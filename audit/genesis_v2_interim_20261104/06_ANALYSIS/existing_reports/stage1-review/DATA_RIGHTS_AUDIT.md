# Stage 3 data rights and plan audit — 2026-11-02

## Frozen plan dry runs

- S1: 130 training runs, 3,120 measurement jobs, 728 structure jobs; `DRY_RUN_NO_SCIENCE`; plan output SHA is recorded by file hash alongside this report.
- S2: 96 training runs, 2,304 measurement jobs, 912 structure jobs; `DRY_RUN_NO_SCIENCE`.
- Outputs: `plan-s1.txt`, `plan-s2.txt` in this directory. No scientific rows, data downloads, or protocol lock were created.

## Source/license review

- Config requests Project Gutenberg eBook #100 `pg100.txt`, leaves `text_expected_sha256: null`, and describes the text as public domain.
- The live eBook source page identifies this digital edition as copyrighted 1990–1993 by World Library, Inc., explicitly says it is not public domain, and limits copying/distribution to personal, noncommercial use. This conflicts with the frozen config's public-domain description; do not use this corpus for the study absent an authorized source correction/new protocol.
- Project Gutenberg's general license says local-country copyright law applies outside the US. The operator is in Singapore; this audit did not establish the local status of the World Library digital edition.
- CIFAR-10 official page (redirects to `cave.cs.toronto.edu/kriz/cifar.html`) describes/releases the dataset but the inspected page does not give a clear dataset license. Dataset download availability is not treated as a license.
- MNIST original source page could not be fetched during this audit; the original source's reusable terms were not independently confirmed. Third-party mirrors/catalogs are not accepted as authority to broaden the original terms.
- Consequently no data was downloaded and neither license acceptance flag was enabled. A broad `--accept-licenses` would be unsafe for the three-source batch.

## Stage gate

`DATA_BLOCKED`: source authorization and immutable versions/hashes are not established for all real datasets. G0 remains blocked because runbook requires Stage 3 data preparation before CUDA G0. No threshold, task, seed, or source was changed.

## Recovery

Before data access, establish permitted exact versions and hashes for the configured corpora. For eBook #100, obtain a confirmed permitted-use source or a separately approved corrected source/protocol; for CIFAR-10 and MNIST, obtain clear original-source terms. Then amend the source/config only under the protocol change-control rules, rerun the manifest/software tests and relevant G0, and record source hashes before protocol freeze. Do not just toggle config booleans.

## Follow-up primary-source check (2026-11-02)

- The MNIST original URL `https://yann.lecun.com/exdb/mnist/` continues to time out/unavailable in web retrieval. Search surfaced secondary mirrors and papers claiming CC BY-SA 3.0, but no accessible current rights-holder terms. No license inferred from those secondary reports.
- CIFAR-10 source page (https://cave.cs.toronto.edu/kriz/cifar.html) says to cite its technical report and publishes archive versions/MD5s, but no grant/license text appears on the inspected original page. Distribution/citation guidance is not treated as a broad license grant.
- Shakespeare #100 remains explicitly marked as a copyrighted digital edition, with personal/noncommercial restrictions. Its terms require local jurisdiction compliance; no Singapore legal determination was made.
- No pre-registered substitute source was found in the repository protocol/config. No source/task was changed.
