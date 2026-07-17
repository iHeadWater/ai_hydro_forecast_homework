# Songliao 多实验结果对比

多轮调整 `rep`、`ngs`、模型或 `kernel_size` 后，手工打开各实验的 CSV、JSON 和
配置文件容易产生抄录错误。`scripts/compare_songliao_experiments.py` 扫描已有结果，
不重新运行模型，并按 NSE 生成统一排名。

## 使用方法

```bash
conda activate hydro_homework
python scripts/songliao_workflow.py compare --basin songliao_21401550
# 或直接运行
python scripts/compare_songliao_experiments.py --basin songliao_21401550
```

常用参数：

- `--results-dir`：实验结果根目录，默认 `hydromodel/results/songliao_event`。
- `--output-dir`：CSV/Markdown 输出目录，默认 `reports`。
- `--no-write`：只在终端打印，不写输出文件。

## 汇总内容

工具读取 `basins_metrics.csv`、`calibration_results.json`、匹配的配置文件和图件目录，
汇总 NSE、KGE、RMSE、Corr、目标函数、`rep`、`ngs`、随机种子、模型、
`kernel_size` 和图件数量。输出为：

```text
reports/songliao_experiment_comparison.csv
reports/songliao_experiment_comparison.md
```

生成文件中的路径相对仓库根目录，便于在不同计算机之间复现。`reports/` 默认被
Git 忽略，避免运行工具后污染代码 PR。
