---
name: songliao-experiment-comparison
description: Compare existing Songliao calibration experiments without rerunning models. Use when selecting the best run, reviewing rep/ngs/kernel_size tuning, ranking NSE/KGE/RMSE results, checking generated figures, or producing reproducible CSV and Markdown experiment summaries.
---

# Songliao experiment comparison

Read existing outputs first. Do not rerun calibration unless the user explicitly asks.

## Procedure

1. From the repository root, run:

   ```bash
   python scripts/compare_songliao_experiments.py --basin songliao_21401550
   ```

2. For custom locations, use `--results-dir` and `--output-dir`. Use `--no-write` for a
   terminal-only check.

3. Read `reports/songliao_experiment_comparison.csv` or the generated Markdown report.

4. Rank primarily by validation NSE. Also report KGE, RMSE, Corr, objective value, `rep`,
   `ngs`, random seed, model, `kernel_size`, and figure counts when available.

5. State that the comparison reads existing files only. Distinguish missing metrics from
   genuinely worse metrics, and do not claim generalization when train/test periods overlap.
