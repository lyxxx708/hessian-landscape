# Asset inventory and provenance manifest

**Repository archive date:** 2026-10-26.
**Discovery:** target GitHub repository was empty before this archive was initialized; accessible Project conversation files yielded no experiment originals; Library and Google Drive searches did not identify these exact Hessian filenames. Searches may not span every legacy chat or local workstation.

## Present in GitHub

- README + docs: **RECONSTRUCTED_DOCUMENTATION** (summarized from user-provided messages; not byte-preserved originals).
- archive/REPORTED_MEASUREMENTS.csv: **TRANSCRIPTION** (selected values extracted from report text; not original logs).
- scripts/reference_block_metrics.py and tests: **NEW_REIMPLEMENTATION** (new independent helper; not historical code).
- requirements.txt, .gitignore: archive support files.

## Historical assets mentioned but NOT provided/found

| File/path (reported name) | Role | Archive status |
|---|---|---|
| dln_inverse_sparsity_mrs.py; dln_forensic_sweep.py; dln_high_precision_ref.py | Phase I–II source | MISSING ORIGINAL |
| dln_rebuttal.py v1.0 | Phase IV code | MISSING ORIGINAL |
| rebuttal_log.json | Phase IV raw run log | MISSING ORIGINAL |
| phase_v_log.json; phase_v_analysis.png | earlier Phase V raw outputs | MISSING ORIGINAL |
| theory_scalar_toy.py; theory_symmetry_breaking.png | later Phase V theory | MISSING ORIGINAL |
| run_phase_v_suite.py | later Phase V experiments | MISSING ORIGINAL |
| phase_v_b_patch.py | Phase V-B patch | MISSING ORIGINAL |
| results_phase_v.pkl; results_phase_v_b.pkl | numerical results | MISSING ORIGINAL |
| fig1_paradox.png; fig2_control.png; fig3_surgery.png; fig5_preconditioner_wars.png; fig_surgery_curve_v_b.png | diagnostic figures | MISSING ORIGINAL |
| genesis_auditor_rev4.py; genesis_rev4_final.pkl | Phase VI Rev4 | MISSING ORIGINAL |
| original full stdout/stderr, environment lock, checkpoint weights, SHA256 manifest | reproducibility | MISSING ORIGINAL |
| original Gemini-generated code blocks named only by UI titles | early proposals | MISSING ORIGINAL |

## Receipt process for original files

1. Verify their real provenance, modification history, license and sensitive information.
2. Compute SHA-256 on local machine; preserve bytes without substitution.
3. Save under originals/<phase>/<original filename>, with sha256 and environment metadata.
4. Large binary pkl checkpoints should be reviewed for unsafe deserialization, size and repository capacity; use Git LFS or signed release archive where appropriate.
5. Record hash, source, author, exact input parameters, linked claims and supersession status.
6. Update docs/CLAIMS_AND_AUDIT.md only after actually rerunning checks.

**No original experiment file or hash has been fabricated in this package.**
