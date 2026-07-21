---
name: songliao-calibration
description: >-
  在本仓库用 hydromodel 对 songliao(松辽)3h 洪水事件数据集做参数率定(calibration)
  与评估(evaluation),核心是修改 hydromodel/configs/songliao_event_3h.yaml 里的参数
  (流域 basin_ids、模型、SCE-UA 迭代次数、训练/测试时段等)来得到不同结果。当用户想:
  率定/评估 songliao、跑 hydromodel、调 songliao_event_3h.yaml 参数、换流域或换模型重跑、
  看 NSE / KGE / RMSE 等指标时,使用本 skill。
---

# songliao 数据集率定与评估

本 skill 指导你用 hydromodel 对 **songliao 3h 洪水事件数据集**做参数率定和评估。
一切围绕一份配置文件 **`hydromodel/configs/songliao_event_3h.yaml`** 展开——
**改这份 yaml 里的参数,就能跑出不同的结果。**

## 前提

- 环境已按 `docs/setup.md` 配好(Python ≥3.11,`pip install -r requirements.txt`
  已把本地 `hydrodatasource/`、`hydromodel/` 以 editable 装好)。
- `data/songliaorrevent/songliaorrevent/` 数据已放入仓库。
- **所有命令都从 `hydromodel/` 目录运行**(config 里 `uri` 是相对该目录的 `../data/...`)。

如果不确定环境是否就位,先验证:
```bash
python -c "import hydromodel, hydrodatasource; print('OK')"
```

## 关键文件与产物位置

| 东西 | 路径(相对 `hydromodel/`) |
|------|--------------------------|
| 配置文件(要改的) | `configs/songliao_event_3h.yaml` |
| 率定脚本 | `scripts/run_event_calibration.py` |
| 评估脚本 | `scripts/run_xaj_evaluate.py` |
| 率定输出目录 | `results/songliao_event/songliao_event_3h/` |
| 评估指标结果 | `results/songliao_event/songliao_event_3h/evaluation_test/basins_metrics.csv` |

## 标准工作流程(4 步)

### 1. 明确用户想改什么参数
先问清楚(或根据用户需求判断)这次要变的是哪个变量:换流域?换模型?加大迭代次数求收敛?
划分训练/测试期?—— 见下方【可调参数速查】。

### 2. 修改 `configs/songliao_event_3h.yaml`
只改需要改的那几行,其余不动。改完把改动向用户说明。

### 3. 跑率定
```bash
cd hydromodel        # 若尚未在此目录
python scripts/run_event_calibration.py --config configs/songliao_event_3h.yaml
```
率定用 SCE-UA 优化,输出参数和损失(loss=RMSE)到
`results/songliao_event/songliao_event_3h/`。**注意:率定本身只给 RMSE,NSE 要下一步评估才有。**

### 4. 跑评估、读指标
```bash
python scripts/run_xaj_evaluate.py \
    --calibration-dir results/songliao_event/songliao_event_3h \
    --eval-period test
```
指标写到 `.../evaluation_test/basins_metrics.csv`,里面有 **NSE / RMSE / KGE / PBIAS**。
读这个 csv 把指标报给用户。`--eval-period` 可选 `test` / `train` / `custom`
(custom 需再加 `--custom-period 起 止`)。

## 可调参数速查(改这些来"得到更多结果")

在 `configs/songliao_event_3h.yaml` 里:

| 参数 | 作用 | 怎么改 |
|------|------|--------|
| `data_cfgs.basin_ids` | 率定哪个/哪些流域 | 换成别的流域 id,或列多个:`["songliao_11000200", "songliao_11001300"]`。有效 id 见下方【如何列出有效流域】 |
| `model_cfgs.name` | 用哪个模型 | **只用 XAJ 系列**(数据是 3h 事件):`xaj`、`xaj_mz`(默认)、`semi_xaj`、`xaj_slw`。**不要用 GR 系列**——它们是日/月尺度,不适配 3h 事件 |
| `model_cfgs.params.kernel_size` | 汇流单位线长度 | 影响洪峰形状,可试 10~20 |
| `training_cfgs.SCE_UA.rep` | 最大迭代次数 | 越大越接近收敛但越慢。快速试跑用 500~1000,正式率定用 5000+ |
| `training_cfgs.SCE_UA.ngs` | 复合形个数 | 增大提升全局搜索能力,默认 10 |
| `training_cfgs.SCE_UA.kstop`/`peps`/`pcento` | 收敛判据 | 收紧(减小 peps/pcento)会更严格但更慢 |
| `data_cfgs.train_period` / `test_period` | 训练 / 测试时段 | 默认两者都是全时段。要做真正的"训练-测试"评估,应把它们分成不重叠的两段 |
| `data_cfgs.warmup_length` | 预热步数 | 事件数据默认 0;连续数据才需要预热 |
| `evaluation_cfgs.metrics` | 输出哪些指标 | 默认 `[NSE, RMSE, KGE, PBIAS]`,可增删 |

**不要改**的项:`time_unit`(只有 `3h` 数据可用)、`reader: floodevent`、`is_event_data: true`、
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

- **找不到数据 / 路径报错**:多半是没从 `hydromodel/` 目录运行,`../data` 指偏了。先 `cd hydromodel`。
- **`FileNotFoundError: attributes.csv`**:说明用的 hydrodatasource 是旧版。本仓库的
  hydrodatasource 已支持 nc 属性 + 可选 basins.shp(commit `436ac80`),确认装的是本地 editable 版
  (`pip show hydrodatasource` 的 Location 指向仓库内)。
- **`FileNotFoundError: ...\.cache\hydrodataset\...attributes.nc`(缓存目录不存在)**:新机器首次运行、
  缓存目录还没建。本仓库 hydrodatasource 已修复(自动建目录);若仍遇到说明用了没打补丁的旧包,临时办法:
  `New-Item -ItemType Directory -Force "$env:USERPROFILE\.cache\hydrodataset"`。
- **NSE 看不到**:率定只出 RMSE;必须再跑第 4 步评估,NSE 才在 `basins_metrics.csv` 里。
- **换成 GR 模型跑不通**:GR 系列是日/月尺度,不适配 3h 事件数据,且评估脚本是 XAJ 专用。
  想比较不同模型时,在 XAJ 系列内部换(xaj / xaj_mz / semi_xaj)。
- **Windows 控制台 emoji 报 `UnicodeEncodeError`**:脚本里有 emoji 打印,设 `PYTHONUTF8=1` 再跑。

## 报告结果给用户

跑完后,读 `basins_metrics.csv`,把这次用的**参数配置**(改了什么)和对应的
**NSE / KGE / RMSE / PBIAS** 一起报给用户,方便对比不同参数下的效果。
