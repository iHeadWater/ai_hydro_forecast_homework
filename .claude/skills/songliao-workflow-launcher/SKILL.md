---
name: songliao-workflow-launcher
description: Run and diagnose the Songliao hydromodel workflow from the repository root through a stable wrapper. Use for environment/path checks, printing equivalent commands, calibration dry-runs, evaluation, visualization, or experiment comparison, especially on Windows, PyCharm, PowerShell, cmd, or Anaconda Prompt.
---

# Songliao workflow launcher

Use `scripts/songliao_workflow.py` as the repository-level entrypoint. It calls the existing
scripts under `hydromodel/` with the required working directory and UTF-8 environment; it
does not replace or modify model code.

## Procedure

1. Run the environment and path check from the repository root:

   ```bash
   python scripts/songliao_workflow.py doctor
   ```

2. If a non-default config is requested, pass its experiment name:

   ```bash
   python scripts/songliao_workflow.py doctor --experiment songliao_event_3h_rep8000
   ```

3. Print platform-specific raw commands when the user needs manual reproduction:

   ```bash
   python scripts/songliao_workflow.py commands --basin songliao_21401550
   ```

4. Use `--dry-run` before calibration when the user only wants command verification:

   ```bash
   python scripts/songliao_workflow.py calibrate --dry-run
   ```

5. Run `calibrate` only with explicit user approval. Evaluation, visualization, and
   comparison can use existing outputs:

   ```bash
   python scripts/songliao_workflow.py evaluate
   python scripts/songliao_workflow.py visualize --basin songliao_21401550
   python scripts/songliao_workflow.py compare --basin songliao_21401550
   ```

Report the interpreter, failed checks, exact command, and output path. Do not silently
change the experiment config or validation period.
