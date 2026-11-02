# Mandatory local storage policy — E: first, minimize C: writes

**Owner instruction:** Prefer E: for as much of GENESIS/Codex GPU research as technically possible; minimize use of the system C: volume. This policy is part of the local full-run research contract, not a request to move the owner's existing personal data.

## Default locations

| Purpose | Required default |
| --- | --- |
| Codex experiment repo / isolated worktree | E:\GENESIS\worktrees\hessian-landscape-revalidation |
| Dedicated Python virtual environment + package installation | E:\GENESIS\venvs\hessian-landscape |
| Public datasets and downloaded source archives | E:\GENESIS\datasets and E:\GENESIS\downloads |
| Python/pip/uv/Hugging Face/PyTorch/CUDA/Triton cache | E:\GENESIS\cache\... |
| Process-scoped temporary and build files | E:\GENESIS\tmp |
| Checkpoints, numerical matrices, raw probe data, SQLite state, figures, logs, final reports | E:\GENESIS\runs\genesis_full_20261102 |

These paths are defaults. Codex may use a different **E:** directory when necessary, but it must record it explicitly and not silently relocate bulk content onto C:. Avoid saving large files in C:\Users\...\Downloads, Desktop, AppData, ProgramData or the default user-level PyTorch/HF cache.

## Safe bootstrap

In the PowerShell process that launches the local training worker, dot-source:

    . .\scripts\prepare_local_e_drive.ps1

This validates that E: is present, creates E: directories and temporarily sets process-level TEMP, TMP, TMPDIR, PIP_CACHE_DIR, UV_CACHE_DIR, HF_HOME, HF_HUB_CACHE, HF_DATASETS_CACHE, TORCH_HOME, TORCH_EXTENSIONS_DIR, TRITON_CACHE_DIR, MPLCONFIGDIR, NUMBA_CACHE_DIR, PYTHONPYCACHEPREFIX, CUDA_CACHE_PATH, XDG_CACHE_HOME and GENESIS_* directory variables. These are inherited by child Python processes, **not** globally persisted for Windows. The generated E:\GENESIS\runs\genesis_full_20261102\storage_preflight.json stores initial volume availability.

**Important:** Running the script in a separate, already-exited PowerShell process does not change another process's environment. The scheduler, all resume/restart workers, and dependency-install commands must launch inside a correctly configured environment or re-run this bootstrap each time. Explicit dataset/cache/artifact root arguments still take precedence over assumptions about environment variables; do not rely on env vars alone.

Create the venv directly on E: before pip install, for example:

    py -3.11 -m venv E:\GENESIS\venvs\hessian-landscape
    E:\GENESIS\venvs\hessian-landscape\Scripts\python.exe -m pip install -r requirements.txt

Use a stable compatible PyTorch CUDA wheel after checking the installed NVIDIA driver. Package downloads and build directories must be directed to E:. If a repository already exists on C:, leave it untouched; use a new E: clone or E: worktree without deleting/moving the original, and avoid duplicating very large artifacts.

For torchvision.datasets and similar libraries, **pass E:\GENESIS\datasets explicitly** as the dataset root. Put model checkpoints and torch.save outputs under the E: run directory. Set experiment output paths in config to absolute E: paths; never rely on a relative path whose working directory could be on C:.

## Disk space preflight and safety rules

1. Before G0, record free/total size for C: and E: (do not assume E: has enough capacity just because GPU time is unlimited).
2. Estimate the maximum and expected disk footprint of S1/S2/S3 from actual pilot artifact size per checkpoint, including model weights, NPZ/JSONL/probe traces, data and cache; record the forecast and disk reserve inside the E: run folder. Update the projection after each family.
3. Before large dataset downloads or each stage, verify E: available capacity. Log E: and C: free-space delta periodically in RESOURCE_ACCOUNTING.md so unexpected C: growth can be detected.
4. If E: is absent, not writable, or out of space, **pause the local runner**, mark STORAGE_BLOCKED and report the expected shortfall. **Never fall back to C: without the owner's explicit approval.**
5. It is acceptable that existing Windows, drivers, paging, the system Python launcher, and the already-installed Codex app may continue to use C: for small unavoidable system-managed files. Do not claim zero C: usage or attempt unsafe Windows-level redirection.
6. Do not change machine-wide TEMP/TMP, Windows profile directories, paging file, driver installations, junctions or system storage policies. Never silently move, clean or delete the owner's C: files. Do not delete scientific evidence on E: to free space without traceable retention/archival policy.
7. Codex itself can have unavoidable application caches under Windows user profile. Never use the app as the high-volume experiment logger. Use the E: Python runner, compact assistant status updates and local E: reports instead of sending raw telemetry to Codex chat.

## Acceptance tests

- G0 emits an E: storage receipt proving configured E: worktree/venv/dataset/temp/cache/run paths exist and are writable.
- Pip, torch, datasets and experiment runs demonstrate that large newly created files are written under E:, not in C: default download/cache directories.
- The run's source and full evidence artifacts all live under E:, unless explicitly documented as harmless unavoidable system artifacts.
- Unexpected significant C: usage or attempts to write bulky data to C: are treated as a resource/configuration issue to repair before the full sweep.
- Every background worker and resume path reloads the E:-first environment; no silent fallback after reboot.

**Precedence:** this policy overrides older relative-directory examples in the earlier draft protocol and project docs. The local full config's absolute E: paths are canonical for this experiment.