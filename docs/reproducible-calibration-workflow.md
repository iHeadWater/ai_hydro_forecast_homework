# 多实验可复现率定工作流

本文档是 `songliao-calibration` skill 的扩展,适用于需要多轮参数对比的场景
(换模型、调 kernel_size、调 rep/ngs 等)。Skill 中的单次 smoke test 流程仍然有效;
本文档提供一套更严格的多实验管理规则,确保结果可复现、可恢复、可比较。

## 1. Safety invariants

以下规则在任何实验中**不得违反**:

- `test_period` 始终保持老师提供的原始值,禁止为提升 NSE 而修改
- `configs/songliao_event_3h.yaml` 是只读基线模板,任何实验不得直接编辑它
- 所有命令从 `hydromodel/` 目录运行
- 指标必须从实际输出文件(`basins_metrics.csv`, `calibration_results.json`)读取,
  不得从屏幕输出推测

## 2. Run ID convention

每个实验必须有唯一 `run_id`,建议格式:

```
<stage>_<model>_k<kernel>_rep<rep>_ngs<ngs>_seed<seed>[_retryN]
```

| 组成部分 | 含义 | 示例 |
|----------|------|------|
| `stage` | 实验阶段 | `smoke`, `screen`, `final` |
| `model` | 模型名 | `xaj`, `xaj_mz` |
| `k<kernel>` | kernel_size | `k15`, `k20` |
| `rep<rep>` | SCE-UA 迭代次数 | `rep500`, `rep8000` |
| `ngs<ngs>` | 复合形个数 | `ngs10`, `ngs20` |
| `seed<seed>` | random_seed | `seed1234` |
| `_retryN` | 可选,中断重试序号 | `_retry1`, `_retry2` |

示例: `screen_xaj_mz_k20_rep1000_ngs10_seed1234`, `final_xaj_mz_k20_rep8000_ngs10_seed1234_retry1`

## 3. Preflight checks

每次启动新实验前检查:

```bash
# 确认在 hydromodel/ 目录
pwd

# 确认 config 路径正确
ls configs/experiments/<run_id>.yaml

# 确认 experiment_name 与 run_id 一致
grep experiment_name configs/experiments/<run_id>.yaml

# 确认输出目录尚不存在或为干净的空目录
ls results/songliao_event/<run_id>/ 2>/dev/null && echo "WARNING: output dir already exists"
```

## 4. Create an independent experiment config

```bash
# 从基线模板复制
cp configs/songliao_event_3h.yaml configs/experiments/<run_id>.yaml

# 编辑副本:设置 experiment_name、调整 model/rep/ngs/kernel_size 等
# 必须保持 test_period 不变
# 使用你习惯的编辑器,或让 AI agent 代为修改
```

## 5. Dry-run, calibration and evaluation

**必须先 dry-run 再正式率定:**

```bash
# dry-run — 验证配置有效
python scripts/run_event_calibration.py --config configs/experiments/<run_id>.yaml --dry-run

# 正式率定 — 看到 "Configuration resolved and validated" 后再执行
python scripts/run_event_calibration.py --config configs/experiments/<run_id>.yaml

# 评估 — 率定完成后立即执行
python scripts/run_xaj_evaluate.py \
    --calibration-dir results/songliao_event/<run_id> \
    --eval-period test
```

率定输出 `calibration_results.json` 和 SCE-UA 轨迹 CSV;
评估输出 `evaluation_test/basins_metrics.csv` 和 NetCDF 结果文件。

## 6. Duplicate-process checks

**同一时间只能运行一个 `run_event_calibration.py`。** 启动前检查:

**Windows PowerShell:**
```powershell
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match "run_event_calibration\.py" } |
    Select-Object ProcessId, Name, CommandLine
```

**Linux / macOS / Git Bash:**
```bash
ps aux | grep "[r]un_event_calibration"
```

如果有进程正在运行,等待其完成后再启动新的率定任务。

## 7. Completion-state checks

率定和评估完成后,确认以下文件存在:

| 文件 | 含义 |
|------|------|
| `results/songliao_event/<run_id>/calibration_results.json` | 率定完成 |
| `results/songliao_event/<run_id>/evaluation_test/basins_metrics.csv` | 评估完成 |

- 两者均存在 → 实验 `completed`
- `calibration_results.json` 存在但 `basins_metrics.csv` 缺失 → 率定完成但未评估,运行评估脚本补全
- `calibration_results.json` 缺失 → 实验 `interrupted`

## 8. Interruption and `_retryN` recovery

率定被中断(进程终止、超时、手动停止)时:

1. **不要删除或覆盖原目录** — 其中可能包含部分 SCE-UA 轨迹,对问题诊断有用
2. 将实验标记为 `interrupted`
3. 使用新 `run_id` 重试:在原名称末尾加 `_retry1`;若再次中断则 `_retry2`
4. 创建对应的新配置文件和输出目录,从头开始率定

示例:
```
final_xaj_mz_k20_rep8000_ngs10_seed1234           ← 率定被中断,目录不完整
final_xaj_mz_k20_rep8000_ngs10_seed1234_retry1    ← 新 run_id,从头重试
```

## 9. `progress_checkpoint.md`

在 `hydromodel/results/` 下维护一个进度文件,至少记录:

- 每个实验的 run_id、状态(completed / interrupted / failed)、关键指标(NSE、KGE 等)
- 当前已测试范围内的最佳结果及对应配置
- 下一次恢复时应执行的第一条命令

示例结构参见 skill 文档。

## 10. `experiment_summary.csv`

在 `hydromodel/results/` 下维护一个汇总 CSV,建议字段:

```
run_id, model, kernel_size, rep, ngs, random_seed,
train_period, test_period,
calibration_RMSE, NSE, KGE, RMSE, Bias,
status, result_path, notes
```

`train_period` 和 `test_period` 为字符串,内部逗号用引号包裹。
空指标用空字段表示,不得用占位符或虚假值。

### CSV validation

写入后必须用以下方式验证(以 Python/pandas 为例):

```python
import pandas as pd
df = pd.read_csv("experiment_summary.csv")
assert df["run_id"].is_unique, "Duplicate run_id found"
assert not df["run_id"].isna().any(), "Missing run_id"
# 检查必要字段存在
required = ["run_id", "model", "kernel_size", "rep", "ngs",
            "NSE", "KGE", "RMSE", "status"]
for col in required:
    assert col in df.columns, f"Missing column: {col}"
print(f"OK: {len(df)} rows, no duplicates")
```

如 `pandas.read_csv()` 抛出 `ParserError`,通常是某行逗号数量不一致,
逐行检查空指标字段的逗号数量是否与表头列数匹配。

## 11. Metric interpretation

| 指标 | 文件来源 | 含义 | 方向 |
|------|----------|------|:----:|
| Cal RMSE | `calibration_results.json` → `objective_value` | 率定阶段 SCE-UA 优化的损失值 | ↓ 越低越好 |
| NSE | `basins_metrics.csv` | 纳什效率系数 | ↑ 越高越好 |
| KGE | `basins_metrics.csv` | Kling-Gupta 效率系数 | ↑ 越高越好 |
| RMSE | `basins_metrics.csv` | 均方根误差 (m³/s) | ↓ 越低越好 |
| Bias | `basins_metrics.csv` | 均值偏差 (m³/s) | → 越接近 0 越好 |

**重要区分**: Cal RMSE 是率定阶段的优化目标,不代表验证期表现。
最终模型选择必须以评估指标(NSE 为主,KGE 为辅)为依据,不能仅看 Cal RMSE。
README 中的评分档次以验证期 NSE 为准。

读取 `basins_metrics.csv` 时使用文件的实际列名。
当前评估脚本输出的列名为 `Bias` 而非 `PBIAS`,不要预设列名。

## 12. Stopping rules

不设武断的固定阈值。是否继续调参应综合考虑:

- **计算预算**: 预计还能运行多少实验,每个实验耗时多长
- **目标档次**: 距 README 中上一评分档还差多少(以 NSE 衡量)
- **边际改善**: 最近几次参数调整带来的 NSE 提升是否在持续减小
- **指标退化**: 某参数调整后 NSE/KGE 是否出现了下降
- **可复现性**: 同一配置重复运行结果是否稳定

停止时保留并报告已测试范围内的最佳配置,
说明这是"当前已测试范围内的最佳结果"而非"全局最优"。

## 13. Windows troubleshooting

- **`UnicodeEncodeError`**: 脚本中的 emoji 在 Windows GBK 编码下报错。
  解决: 终端中先执行 `export PYTHONUTF8=1`(Git Bash) 或 `$env:PYTHONUTF8="1"`(PowerShell)。
- **路径分隔符**: Git Bash 中可使用正斜杠 `/`,与 Linux/macOS 一致。
- **`FileNotFoundError` 涉及 `.cache`**: 首次运行可能需要手动创建缓存目录,
  详见 SKILL.md "常见坑"节。

## 14. Submission and Git boundaries

- **不要提交**到上游 PR: 个人实验数据、NetCDF 文件、`hydromodel/results/` 目录、
  `data/` 目录、`data+code.zip`、API 密钥、个人邮箱或本机绝对路径。
- `hydromodel/`, `hydrodataset/`, `hydrodatasource/`, `data/` 均在 `.gitignore` 中,
  Git 操作会自动排除。
- 可提交的内容: `.claude/skills/`、`docs/`、`README.md` 等文档改进。
