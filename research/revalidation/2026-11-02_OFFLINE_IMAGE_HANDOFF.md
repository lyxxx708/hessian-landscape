# GENESIS v2 Stage 3 — owner-licensed offline MNIST and CIFAR-10 handoff

**2026-11-02. Status: IMAGE_IMPORT_IMPLEMENTED_NOT_RUN_LOCALLY.** The owner has confirmed the existing MNIST/CIFAR-10 archives are licensed for local research use. This is not authorization to redistribute the images or checkpoints. Do not repeat the open-licence review for these two sources.

## Source rules

Use the two exact absolute local input paths provided by the owner to the Codex Goal. Do not insert C: user-directory strings into public Git history. Inputs stay unchanged and read-only. The importer copies originals and writes prepared training/validation/test tensors, hashes, manifests and all temporary data under E:\GENESIS.

MNIST source: four official IDX .gz images/labels files in the MNIST/raw directory. CIFAR-10 source: data_batch_1 through data_batch_5, test_batch and batches.meta inside cifar-10-batches-py. The optional README and .tar.gz are not needed.

The import code checks each original file against the canonical torchvision MD5 values, generates SHA256 for each, verifies the C: to E: copy and only then decompresses/loads. MNIST IDX magic/count/dimensions and CIFAR uint8 10000x3072 arrays/labels are qualified. CIFAR Python pickle allows only a restrictive set of NumPy/codec globals; arbitrary imports are blocked. This is a local offline import, not a new download.

## Local Codex command (run from the E: worktree's implementation/genesis-v2)

~~~powershell
. .\scripts\genesis_env.ps1
$Py = 'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe'
$MNIST = '<owner-supplied absolute path ending with \MNIST\raw>'
$CIFAR = '<owner-supplied absolute path ending with \cifar-10-batches-py>'
$Run = 'E:\GENESIS\runs\genesis_full_v2'

& $Py -m genesis_gpu --config configs\study_v2.yaml --root $Run import-local-images --mnist-raw $MNIST --cifar-batches $CIFAR --confirm-authorized-local-use
if ($LASTEXITCODE -ne 0) { throw 'LOCAL_IMAGE_IMPORT_BLOCKED: examine the actual error receipt' }
~~~

This command is only available after this new review branch is integrated into a separate, controlled local E: worktree. If source code changes, rerun applicable tests and real CUDA G0 before any protocol freeze; do not alter an already frozen protocol.

## Inspect generated E: artifacts

~~~powershell
Test-Path E:\GENESIS\datasets\genesis_v2\mnist\data.safetensors
Test-Path E:\GENESIS\datasets\genesis_v2\cifar10\data.safetensors
Get-Content E:\GENESIS\runs\genesis_full_v2\datasets\local_image_import_receipt.json -Raw
Get-Content E:\GENESIS\datasets\genesis_v2\mnist\manifest.json -Raw
Get-Content E:\GENESIS\datasets\genesis_v2\cifar10\manifest.json -Raw
~~~

Expected fixed splits, identical to the existing code: MNIST 55000/5000/10000 grayscale uint8 1x28x28; CIFAR-10 45000/5000/10000 RGB uint8 3x32x32, integer labels 0–9, split RNG seed 20261102. Test images never enter training. SHA256 covers originals and prepared safetensors. Identical re-import is idempotent; mismatched archive hashes, corrupted prepared bytes, incomplete data, insufficient E: space or an existing protocol lock are hard failures. No silent C: fallback; no C: source mutation.

## What is and is not unblocked

MNIST/CIFAR image-source gates can now move to IMAGE_DATASETS_READY. **The independent Shakespeare-text source gate remains unresolved** until actual rights/notice assessment and an approved, pinned local text. The tentative First Folio #2270 change in PR #13 is not silently accepted by this image import. Accordingly the combined state is IMAGE_DATASETS_READY_TEXT_PENDING, NOT whole-study DATA_READY, G0_PASS or S1_EXECUTED.

Once the text is separately approved and prepared, complete the dataset manifest and source SHA256 receipts. Then run both software/legacy test suites, the genuine RTX 4070 Ti numerical G0, source/config/data/seed freeze, and the finite S1=130/S2=96 run plan. S3 remains conditional on U/P gates. Never publish user directory paths, raw data, credentials or local checkpoint files.

**Evidence boundary:** This PR supplies tested code and an execution handoff; it does not claim the real Windows inputs were read by ChatGPT or the GPU study was started.
