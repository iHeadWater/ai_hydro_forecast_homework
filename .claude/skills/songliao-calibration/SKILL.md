---
name: songliao-calibration
description: >-
  在本仓库用 hydromodel 对 songliao(松辽)3h 洪水事件数据集做参数率定(calibration)
  与评估(evaluation)。songliao_event_3h.yaml 是只读基线模板,实验时复制为独立配置,
  可调整 basin_ids、模型、SCE-UA 迭代次数等;test_period 固定、禁止修改。
  当用户想: 率定/评估 songliao、跑 hydromodel、换流域或换模型重跑、
  看 NSE / KGE / RMSE 等指标时,使用本 skill。
---

# songliao 数据集率定与评估

本 skill 指导你用 hydromodel 对 **songliao 3h 洪水事件数据集**做参数率定和评估。
**改配置文件里的参数,就能跑出不同的结果。**

## 前提

- 环境已按 `docs/setup.md` 配好(Python ≥3.11,`pip install -r requirements.txt`
  已把本地 `hydrodatasource/`、`hydromodel/` 以 editable 装好)。
- `data/songliaorrevent/songliaorrevent/` 数据已放入仓库。
- **所有命令都从 `hydromodel/` 目录运行**(config 里 `uri` 是相对该目录的 `../data/...`)。

如果不确定环境是否就位,先验证:
```bash
python -c "import hydromodel, hydrodatasource; print('OK')"
```

### Windows 用户：首次运行前必须设置 UTF-8

脚本中包含 emoji 输出,Windows 默认 GBK 编码会报 `UnicodeEncodeError`。**在运行任何率定或评估命令之前**执行:

- **Git Bash**: `export PYTHONUTF8=1`
- **Windows CMD**: `set PYTHONUTF8=1`
- **PowerShell**: `$env:PYTHONUTF8="1"`

建议直接加到终端启动配置中,避免每次手动设置。

## 关键文件与产物位置

| 东西 | 路径(相对 `hydromodel/`) |
|------|--------------------------|
| 基线配置(只读模板) | `configs/songliao_event_3h.yaml` |
| 实验配置目录 | `configs/experiments/` |
| 率定脚本 | `scripts/run_event_calibration.py` |
| 评估脚本 | `scripts/run_xaj_evaluate.py` |
| 率定输出目录 | `results/songliao_event/<experiment_name>/` |
| 评估指标结果 | `results/songliao_event/<experiment_name>/evaluation_test/basins_metrics.csv` |

## 工作流程

### 单次快速试跑(smoke test)

适合第一次验证流程是否跑通。

**1. 复制基线配置**

`configs/songliao_event_3h.yaml` 是老师提供的基线模板,**不要直接修改**。
复制到实验目录:

```bash
cp configs/songliao_event_3h.yaml configs/experiments/<run_id>.yaml
```

**2. 修改副本**

只改需要改的那几行,其余不动。**必须保持 `test_period` 为老师提供的原始值,不得修改。**
`train_period` 只有在作业明确允许且用户明确要求时才能调整,调整后必须在实验记录中注明。

在副本中设置 `experiment_name` 与 `run_id` 一致,确保输出目录唯一。

**3. 率定前 dry-run**

```bash
python scripts/run_event_calibration.py --config configs/experiments/<run_id>.yaml --dry-run
```

验证 `Configuration resolved and validated` 后再正式运行。

**4. 跑率定**

```bash
python scripts/run_event_calibration.py --config configs/experiments/<run_id>.yaml
```

率定用 SCE-UA 优化,输出参数和损失(loss=RMSE)到
`results/songliao_event/<experiment_name>/`。**率定本身只给 RMSE,NSE 要下一步评估才有。**

**5. 跑评估、读指标**

```bash
python scripts/run_xaj_evaluate.py \
    --calibration-dir results/songliao_event/<experiment_name> \
    --eval-period test
```

指标写到 `.../evaluation_test/basins_metrics.csv`。**读取指标时必须使用 CSV 的实际列名**:
当前评估脚本输出列名为 `Bias`、`RMSE`、`ubRMSE`、`Corr`、`R2`、`NSE`、`KGE`、`FHV`、`FLV`,
不要预设列名(例如文档示例中曾出现的 `PBIAS`,实际输出为 `Bias`)。
`--eval-period` 可选 `test` / `train` / `custom`(custom 需再加 `--custom-period 起 止`)。

### 多实验安全模式

当需要多轮参数对比(换模型、调 kernel_size、调 rep/ngs 等)时,
单次流程容易出现基线被覆盖、结果被覆盖、中断无法恢复等问题。
请遵循完整的可复现工作流:详见
**[多实验可复现率定工作流](../../../docs/reproducible-calibration-workflow.md)**。

核心安全规则摘要:

- **唯一 run_id**: 每个实验一个唯一标识,格式建议 `<stage>_<model>_k<kernel>_rep<rep>_ngs<ngs>_seed<seed>[_retryN]`
- **独立 YAML 和输出目录**: 通过 `experiment_name` 确保每个实验结果不互相覆盖
- **dry-run 先行**: 任何长时间率定前先 `--dry-run`
- **不重复启动进程**: 启动前检查是否已有 `run_event_calibration.py` 在运行
- **中断不覆盖**: 中断的实验目录保留,使用 `_retry1`、`_retry2` 新目录重试
- **维护 checkpoint 和 summary**: `progress_checkpoint.md` 和 `experiment_summary.csv` 统一管理所有实验状态和指标
- **指标来自文件**: 禁止根据屏幕输出推测,必须从 `basins_metrics.csv` 实际读取
- **固定 test_period**: 无论单次还是多实验,`test_period` 始终不改

## 可调参数速查

在实验配置文件里:

| 参数 | 作用 | 怎么改 |
|------|------|--------|
| `data_cfgs.basin_ids` | 率定哪个/哪些流域 | 换成别的流域 id,或列多个:`["songliao_11000200", "songliao_11001300"]`。有效 id 见下方【如何列出有效流域】 |
| `model_cfgs.name` | 用哪个模型 | **只用 XAJ 系列**(数据是 3h 事件):`xaj`、`xaj_mz`。`semi_xaj` 在当前 hydromodel 版本中可能无法通过 SCE-UA 率定,如遇到报错应保留真实错误信息并标记为 failed。**不要用 GR 系列**——它们是日/月尺度,不适配 3h 事件 |
| `model_cfgs.params.kernel_size` | 汇流单位线长度 | 影响洪峰形状,可试 10~20 |
| `training_cfgs.SCE_UA.rep` | 最大迭代次数 | 越大越接近收敛但越慢。快速试跑用 500~1000,正式率定用 5000+ |
| `training_cfgs.SCE_UA.ngs` | 复合形个数 | 增大提升全局搜索能力,默认 10 |
| `training_cfgs.SCE_UA.kstop`/`peps`/`pcento` | 收敛判据 | 收紧(减小 peps/pcento)会更严格但更慢 |
| `data_cfgs.train_period` | 训练时段 | **仅在作业允许且用户明确要求时调整**,调整后必须记录 |
| `data_cfgs.warmup_length` | 预热步数 | 事件数据默认 0;连续数据才需要预热 |
| `evaluation_cfgs.metrics` | 输出哪些指标 | 默认 `[NSE, RMSE, KGE, PBIAS]`,可增删 |

**不要改**的项:`test_period`(固定验证期,禁止修改)、`time_unit`(只有 `3h` 数据可用)、`reader: floodevent`、`is_event_data: true`、
`uri`(除非数据搬了地方)。

### 如何列出有效流域 id
数据里有 18 个流域时序,但只有 16 个有属性;`read_object_ids()` 只返回有属性的那 16 个。
需要有效 id 列表时:
```python
from hydrodatasource.reader.floodevent import FloodEventDatasource
ds = FloodEventDatasource(uri="../data/songliaorrevent/songliaorrevent", time_unit=["3h"])
print(ds.read_object_ids())
```

## 常见坑

- **Windows emoji 报错**: 见上方「前提」中的 UTF-8 设置,必须在首次运行前执行。
- **找不到数据 / 路径报错**:多半是没从 `hydromodel/` 目录运行,`../data` 指偏了。先 `cd hydromodel`。
- **`FileNotFoundError: attributes.csv`**:说明用的 hydrodatasource 是旧版。本仓库的
  hydrodatasource 已支持 nc 属性 + 可选 basins.shp,确认装的是本地 editable 版
  (`pip show hydrodatasource` 的 Location 指向仓库内)。
- **`FileNotFoundError: ...\.cache\hydrodataset\...attributes.nc`(缓存目录不存在)**:新机器首次运行、
  缓存目录还没建。本仓库 hydrodatasource 已修复(自动建目录);若仍遇到说明用了没打补丁的旧包,临时办法:
  `New-Item -ItemType Directory -Force "$env:USERPROFILE\.cache\hydrodataset"`。
- **NSE 看不到**:率定只出 RMSE;必须再跑评估步骤,NSE 才在 `basins_metrics.csv` 里。
- **换成 GR 模型跑不通**:GR 系列是日/月尺度,不适配 3h 事件数据,且评估脚本是 XAJ 专用。
  想比较不同模型时,在 XAJ 系列内部换。
- **指标列名不是 PBIAS**:当前 `basins_metrics.csv` 的实际列名是 `Bias`(均值偏差,m³/s),
  不是 `PBIAS`(百分比偏差)。读取 CSV 时使用实际表头。
- **中断的实验目录不完整**:如果 `calibration_results.json` 或 `evaluation_test/basins_metrics.csv`
  缺失,该实验为 interrupted,不要当作有效结果。使用新 `_retry1` 目录重试,不覆盖原目录。

## 指标解读

率定和评估涉及多个指标,含义不同:

| 指标 | 来源 | 含义 | 判断方向 |
|------|------|------|----------|
| Cal RMSE | `calibration_results.json` 的 `objective_value` | SCE-UA 优化目标,率定阶段的拟合误差 | 越低越好,但**不能单独用于选最终模型** |
| NSE | `basins_metrics.csv` | 纳什效率系数,衡量模拟与观测的吻合度 | 越高越好(范围 -∞ ~ 1) |
| KGE | `basins_metrics.csv` | Kling-Gupta 效率系数,综合相关性、偏差和变异性 | 越高越好(范围 -∞ ~ 1) |
| RMSE | `basins_metrics.csv` | 均方根误差(m³/s) | 越低越好 |
| Bias | `basins_metrics.csv` | 均值偏差(m³/s),反映系统性高估或低估 | 越接近 0 越好 |

**以验证期 NSE 为主要评判标准**(与 README 评分档次对齐),KGE 为辅助参考。
Cal RMSE 低不代表验证期 NSE 高,最终模型选择必须基于评估指标而非率定阶段的损失值。

## 报告结果给用户

跑完后,读 `basins_metrics.csv`,使用 CSV 的实际列名,把这次用的**参数配置**(改了什么)和
对应的**NSE / KGE / RMSE / Bias** 一起报给用户,方便对比不同参数下的效果。

如果用户在短时间内跑了多个实验,建议汇总为对比表,标出 NSE 最高者,并说明这是**当前已测试范围内的最佳结果**。
某模型在本次环境或配置下失败,只记录真实错误,不能由此断言该模型"永久不支持"或"全局不可用"。
