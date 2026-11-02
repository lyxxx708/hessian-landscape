# GENESIS v2 — Stage 3 source rights & version recovery (review proposal)

**Date:** 2026-11-02. **Status:** SOURCE_REVIEW_ONLY / NOT A LICENCE GRANT / NOT EXECUTED.  
**Base:** PR #11 `research/fresh-curvature-revalidation-v1-20261102`, source HEAD `6693dde3f0049620b4250b4982f1c6ef43cbefa3`.  
**Purpose:** resolve a pre-freeze source issue without compromising model, training-seed, numerical or claim gates. The owner-provided local evidence says Windows Python 3.11.14, torch 2.10.0+cu128, CUDA 12.8, RTX 4070 Ti, 80/1 v2 tests, and 17/17 legacy tests; **G0/S1/S2/S3 have not run**. Do not republish the local diagnostic ZIP, user paths or hardware identifiers to this public repository.

## 1. What the source audit establishes — and what it does NOT

| Source | Relevant primary or provider evidence | Admissible conclusion for a local noncommercial research run | Remaining restriction |
| --- | --- | --- | --- |
| **MNIST** | [Keras official documentation](https://keras.io/api/datasets/mnist/) expressly identifies copyright holders Yann LeCun and Corinna Cortes and **CC BY-SA 3.0** terms | Licenced use with attribution and required share-alike compliance where applicable; record exact image bytes and authorship | Keras docs are a provider confirmation, not the inaccessible original MNIST homepage. Keep attribution/terms in the run metadata; do not automatically publish raw dataset |
| **CIFAR-10** | [Original distributor/author page](https://www.cs.toronto.edu/~kriz/cifar.html) provides official archives, MD5 values and asks dataset users to cite the technical report | Official site actively supports use as a **research benchmark**; this is a reasonable basis to consider a local noncommercial academic evaluation with citation and no raw redistribution | The inspected page does **not** state a general CC/MIT licence or unrestricted redistribution rights. Neither an official download nor a citation request proves an unrestricted licence. If the project requires an explicit rights grant for *all* data, this source remains **REQUIRES_RIGHTS_DECISION**, not silently approved |
| **Shakespeare eBook #100 (configured legacy)** | [PG catalog](https://www.gutenberg.org/ebooks/100) currently marks it **public domain in the USA**; the embedded [historical digital edition](https://www.gutenberg.org/cache/epub/100/pg100.html) has a 1990–1993 World Library notice. [PG's own Shakespeare help](https://www.gutenberg.org/help/shakespeare.html) reports 2023 metadata changes for older World Library transcriptions | These statements must be interpreted as different **edition/rights metadata**, not resolved by choosing whichever says the desired result | Do not infer a universal country-wide redistribution licence from the US catalog. PG general [licence](https://www.gutenberg.org/policy/license.html) advises non-US users to check their own law |
| **Shakespeare First Folio, eBook #2270 (proposed substitute)** | [PG catalog](https://www.gutenberg.org/ebooks/2270) describes a 1623 First Folio and marks its eBook public domain in the USA; publication record updated 2025 | A **prospective, same-kind character-level Shakespeare-language modelling corpus** with clearer catalog provenance; text, edition, spelling and difficulty are different and must be openly recorded | US status does not certify every local jurisdiction. Inspect actual downloaded notice and apply PG trademark/licence conditions. This change is BEFORE science data freeze, not a replay of old results |
| **EuroSAT RGB (conditional CIFAR alternative)** | [Dataset creator repository](https://github.com/phelber/EuroSAT) states MIT dataset licence; [creator-hosted Zenodo record](https://zenodo.org/records/7711810) publishes EuroSAT_RGB.zip and its MD5 `f46e308c4d50d4bf32fedad2d3d62f3b` | The stronger explicit MIT source can support a prospective vision-arm replacement when the goal demands explicit public licensing | **Changes dataset distribution/domain, sizes and split assumptions. Must create a new pre-registered study version and 32×32 resizing/split adapter**; do NOT silently relabel EuroSAT as CIFAR-10 or claim identical benchmarks |

This is not legal advice or a blanket licence acceptance. Owner/operator authorization must match the intended use, actual jurisdiction, attribution and no-redistribution policy. Permission to download data for research is narrower than permission to redistribute datasets or third-party text.

## 2. Pre-freeze change-control policy

**Safe default for the existing 226-run scientific design:**

1. Retain model families, depths, losses, optimizers, 26×5 discovery settings and 6×16 confirmatory anchor settings. Neither old 2025 matrices nor new experimental outcomes are a target for source selection.
2. Retain original MNIST under CC BY-SA 3.0 with proper attribution and versioned torchvision archive hash.
3. Keep CIFAR-10 as a **separately recorded local-research-use decision**, with the official author's download/citation notice and explicit note `licence_not_identified=true`. If the project's strict policy insists on an explicit licence, do **not** assert CIFAR-10 is MIT or CC and do **not** run it; separately review a EuroSAT MIT **v2.1** variant, with all ResNet analyses renamed and all sample counts/splits fixed before S1.
4. Avoid the old contested #100 eText for new work. The accompanying proposed code correction points the **new** text-source candidate to PG #2270. This remains a Shakespeare character-level LM but must be identified as `First Folio / Gutenberg #2270`; no claim of identical dataset to #100 is allowed. If its exact embedded terms/local rights are unsuitable, suspend the text arm rather than silently selecting another corpus.
5. Lock model configs, source URLs, rights basis, download archive bytes, prepared corpus SHA256, token vocabulary, split indices, and full source/software hashes **after** permitted initial download and **before** any S1 checkpoint is generated. The first-download SHA cannot logically be prespecified unless an authoritative upstream checksum already exists; this is a **two-phase provenance** sequence, not relaxed reproducibility.
6. Keep `--accept-licenses` **disabled until each of the three source categories has a separately documented decision**. A single CLI switch is not a substitute for the per-source review. Do not change a boolean to conceal an unresolved licence. Local Codex must save a source decision receipt with `source_uri`, intended local use, notice, author/owner, rights basis, decision time, raw SHA, prepared SHA, no-raw-upload policy and limitation.
7. Before any science starts, run changed-code tests + all 80 v2 tests and legacy regression, re-run data manifest checks and **actual CUDA G0**, then freeze **new** protocol/source hash and seed manifest. Do not continue from an old protocol lock after source correction.

## 3. Exact operational conditions for Codex

- **At present:** `DATA_BLOCKED` is a valid honest stop; do not mark G0 or training complete. The corrected E: runtime and hardware tests already passed and should not be labelled broken again.
- **Permission and version review:** inspect real source terms; for CIFAR, distinguish *published research use* from *unrestricted licence*. A documented research-only owner decision can be considered, not forged. For stricter explicit licences, prepare a separately labelled EuroSAT v2.1 project instead of silently replacing CIFAR.
- **First permitted downloads:** use existing E:\GENESIS dataset and temporary directories, inspect actual content notices and compute SHA256 immediately. Published upstream MD5 values (CIFAR, EuroSAT) provide additional integrity checks but do not replace SHA256.
- **Reproducibility:** store byte hashes and provenance before protocol freeze; never download a changed upstream version silently after freeze. Local media may remain private while the public repository only receives compact SHA/source notices.
- **Review:** this PR is a **proposed pre-G0 scientific input correction**, not permission to bypass source checks. Keep it reviewable, do not merge automatically, and do not overwrite the running local worktree.

## 4. Exact scope and stop conditions

- Old 2025 Hessian numerical claims remain **RETIRED_AS_EVIDENCE**.
- `DATA_READY` can only follow a documented use-rights decision **for every actually configured dataset**, verified raw archive versions, SHA receipts and prepared-split identities. `DATA_READY` alone is not `G0_PASS`.
- A blocked single dataset is not reason to fabricate an S2 scientific PASS on a synthetic substitute. It may be possible to run separately labelled G0 math/preflight controls, but **S1/S2 scientific coverage stays blocked** until all configured sources qualify.
- No paid cloud/API use, no C: storage fallback, no private raw uploads and no automatic main merge.

**Evidence classes:** `AUTHOR_PROVIDER_SOURCE_REVIEW` → `PERMITTED_DOWNLOAD_WITH_PROVENANCE` → `PREPARED_DATA_SHA_VERIFIED` → `CUDA_G0_VALID` → `PROTOCOL_FROZEN` → S1/S2. These are distinct statuses, not one “PASS”.
