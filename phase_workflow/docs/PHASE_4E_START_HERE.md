# Phase 4E — Literature, novelty and evidence validation

This is the review-facing package for the simulation-only M.Tech project **AI-Driven RTL Test Generation, Coverage Analysis and Verification**.

## Files

- `Phase_4E_Literature_and_Novelty_Report.docx` — editable seven-page report.
- `Phase_4E_Literature_and_Novelty_Report.pdf` — PDF reading copy.
- `Phase_4E_Literature_and_Novelty_Report.md` — version-control-friendly markdown.
- `Phase_4E_Evidence_Audit.py` — offline, read-only audit of the WSL experiment result JSON; `--write` writes new derived, phase-based research evidence files only.
- `SHA256SUMS.txt` — SHA-256 digests for the files above.

## Safe installation

Work in the Ubuntu WSL project root. Keep all prior phase and historical evidence intact. The following command installs the new script and copies the review file(s); if an output filename already exists, stop and inspect it before replacing. It does not edit RTL, testbench generators, prior results, or library files.

```bash
cd ~/Mtech_project/AI_RTL_Verification || exit 1
python3 -m py_compile phase_workflow/tools/phase4e_evidence_audit.py
python3 phase_workflow/tools/phase4e_evidence_audit.py --dry-run
python3 phase_workflow/tools/phase4e_evidence_audit.py --write
python3 phase_workflow/tools/final_audit.py
```

## Evidence hierarchy

The literature report cites externally verified DOI metadata and explains how published methods overlap with this project. The WSL script checks the user's original experiment JSONs and emits an evidence trace. A passing check is **not** proof of publication-level novelty or exhaustive RTL correctness.

## Next phases

- **4F:** update thesis and first/final review slides, figures and project walkthrough using phase names rather than dates/days.
- **4G:** clean-environment repository reproducibility, secrets scan, license/technology-library redistribution review, final manifest, submission ZIP.
