# GENESIS v2 — Stage 3 text-source gate

**State: `IMAGE_DATASETS_READY_TEXT_PENDING` / `INCOMPLETE_BLOCKED_EVIDENCE`.**

## Candidate evidence

The configured URL `https://www.gutenberg.org/cache/epub/2270/pg2270.txt` was fetched over normally verified HTTPS into E: only. The candidate is 4658981 bytes, SHA-256 `f7903c30b83ccaaef85f024746c693a6f7f63c1c926075c998ea67c4732680a4`, UTF-8, and retains the full Project Gutenberg notice and license. Its header states the non-US local-law condition; the footer contains the full license. The file remains a candidate and has not been prepared into model splits or used for training.

The official catalog describes *Shakespeare's First Folio* as a 1623 work by William Shakespeare (1564–1616), first released on Gutenberg in 2000 and last updated 2025, and marks it public domain in the USA. Project Gutenberg requires non-US users to check local law and disclaims making that determination for them. Singapore Copyright Act 2021 §119 provides a 25-year term after the end of first-publication year for qualifying published editions. This supports a plausible local-use basis in 2026, but applying it to this specific edition is an inference, not legal advice or owner/operator authorization.

Primary references: [Gutenberg eBook 2270](https://www.gutenberg.org/ebooks/2270), [Project Gutenberg License](https://www.gutenberg.org/policy/license), [Singapore Copyright Act 2021](https://sso.agc.gov.sg/Act/CA2021). Detailed capture: `E:\GENESIS\evidence\stage3-image-import\gutenberg_text_candidate_rights.json`.

## Current gate

- Owner/operator local-use decision for this exact text/jurisdiction: **pending**.
- Attribution and no-redistribution condition: recorded as study policy; raw source remains private on E:.
- Candidate SHA: pinned in the local evidence receipt, **not yet pinned into the study config**.
- Prepared text splits and combined three-source manifest: **not created**.
- CUDA G0, protocol freeze, S1=130, S2=96, S3 and scientific verification: **not run**.

MNIST/CIFAR owner-confirmed local-use permission remains valid and is not being re-investigated.

## Safe resume

After the owner/operator confirms the exact candidate may be used locally under the recorded attribution/no-redistribution conditions: set the candidate SHA in the pre-freeze config; run the configured `prepare-data` path to create the text split and complete source manifest; verify all data hashes; rerun software and legacy regression; then run real CUDA G0. Freeze only after full DATA_READY and G0 pass. Keep S1=130 and mandatory fresh-seed S2=96 unchanged.
