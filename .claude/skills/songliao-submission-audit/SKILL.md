---
name: songliao-submission-audit
description: Audit Songliao course outputs without rerunning calibration. Use before submission to verify config, calibration JSON, metrics, parameters, scatter and flood-event figures, an optional FDC, NSE threshold, and user-specified report or PR files.
---

# Songliao submission audit

Use `scripts/check_songliao_submission.py` after calibration and evaluation have completed.

## Procedure

1. Audit the standard experiment from the repository root:

   ```bash
   python scripts/check_songliao_submission.py
   ```

2. Pass a custom experiment and threshold when required:

   ```bash
   python scripts/check_songliao_submission.py \
     --experiment songliao_event_3h_rep8000 \
     --basin songliao_21401550 \
     --nse-threshold 0.55
   ```

3. Require user-specific deliverables explicitly rather than guessing filenames:

   ```bash
   python scripts/check_songliao_submission.py \
     --report path/to/report.docx \
     --pr-file path/to/pr-notes.md
   ```

4. Use `--require-fdc` only when an FDC is part of the requested deliverables.

Report all failed paths and metrics. Do not rerun calibration to repair missing outputs
unless the user separately approves that long-running action.
