# 操作示例

> 以下是用内置 **songliao-calibration** skill 完成率定的对话示例。
> **核心玩法：改 `hydromodel/configs/songliao_event_3h.yaml` 的参数，跑出不同结果。**
> 你只管用自然语言说需求，skill 会自动改配置、跑率定+评估、读指标。

## 示例一：第一次率定 songliao

### 第一轮：了解项目

**你**:
> "你好，看看这个项目能做什么，songliao 数据集有哪些流域可以率定？"

**AI 可能回复**:
> 这个项目用 hydromodel 对 songliao 松辽 3h 洪水事件数据做率定。数据是降雨-径流事件，
> 适配 XAJ 系列模型（xaj / xaj_mz / semi_xaj）。共约 16 个可率定流域。率定配置在
> `hydromodel/configs/songliao_event_3h.yaml`，改里面的参数就能跑出不同结果。

### 第二轮：跑一次率定 + 评估

**你**:
> "帮我率定 songliao，用默认配置，跑完把 NSE 报给我"

**AI 会做的事**（skill 自动执行）：
1. 从 `hydromodel/` 目录跑 `python scripts/run_event_calibration.py --config configs/songliao_event_3h.yaml`（SCE-UA 优化）
2. 再跑 `python scripts/run_xaj_evaluate.py --calibration-dir results/songliao_event/songliao_event_3h --eval-period test`
3. 读 `basins_metrics.csv`，汇报指标：

```
流域 songliao_11000200（xaj_mz，rep=5000）：
| 指标  | 值     |
|-------|--------|
| NSE   | 0.47   |
| RMSE  | 1.37   |
| KGE   | 0.55   |
| PBIAS | -8.2%  |
```

> 提示：率定本身只给 RMSE，**NSE 要跑评估这一步才有**。

### 第三轮：换流域

**你**:
> "换成 songliao_11001300 这个流域再跑一次，和上一个对比"

**AI 会**改 config 里的 `data_cfgs.basin_ids` 为 `["songliao_11001300"]`，重跑率定+评估，
把两个流域的 NSE 并列给你。（不知道有哪些有效流域时，可以让 AI 用
`ds.read_object_ids()` 列出那 16 个。）

### 第四轮：加大迭代次数求收敛

**你**:
> "把 SCE-UA 的 rep 调到 8000 求更接近收敛，重跑，看看 NSE 有没有提升"

**AI 会**改 `training_cfgs.SCE_UA.rep` 为 `8000`，重跑，对比前后 NSE 和耗时。

## 示例二：换模型对比（限 XAJ 系列）

**你**:
> "在同一个流域上分别用 xaj 和 xaj_mz 率定，对比 NSE 和 KGE"

**AI 会**依次把 `model_cfgs.name` 改成 `xaj`、`xaj_mz` 各跑一次，生成对比表。

> ⚠️ 只在 XAJ 系列内换（xaj / xaj_mz / semi_xaj）。GR 系列是日/月尺度，不适配 3h 洪水
> 事件；评估脚本也是 XAJ 专用。

## 示例三：多流域批量率定

**你**:
> "对下面三个流域分别做 xaj_mz 率定，最后汇总每个流域的 NSE：
> - songliao_11000200
> - songliao_11001300
> - songliao_11002620"

**AI 会**逐个改 `basin_ids` 跑率定+评估，最后汇总一张表。

> 覆盖越多流域、达标（NSE ≥ 0.40）越多，成绩档次越高——这正是评分的核心。

## 示例四：结果不理想时调试

**你**:
> "这个流域验证期 NSE 只有 0.3，太低了。帮我分析可能原因，然后试试：
> 1. 把 rep 加大到 8000
> 2. 换成 xaj_mz 模型
> 3. 调一下 kernel_size（试 12 和 18）"

**AI 会**逐项修改 config 重跑，并分析哪个改动对 NSE 提升最明显。

## 关键要点

1. **一切围绕那份 yaml**：`songliao_event_3h.yaml` 里改参数（流域 / 模型 / rep / 时段 / kernel_size）就能得到不同结果。
2. **从 `hydromodel/` 目录跑**：config 里 `uri` 是相对路径 `../data/...`，跑错目录会找不到数据。
3. **NSE 要评估才有**：率定只出 RMSE，记得让 AI 跑第二步评估。
4. **报错就贴回去**：任何错误信息直接贴给 AI，让它诊断修复。
5. **记录好参数与结果**：把每次的参数配置和对应 NSE 记下来，方便对比、写报告。
