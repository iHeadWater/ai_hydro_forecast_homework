# AI Hydro Forecast Homework

> 本科生实习课程：使用 AI Agent 工具辅助水文模型率定

## 关于本项目

本仓库不是代码库，而是一个 **AI Agent Skill 项目**——它提供文档、配置和教程，帮助学生用自然语言对话的方式，通过 Claude Code / OpenCode 等 AI Agent 工具调用水文模型，完成模型率定任务。

实际的水文模型代码**不随本仓库分发**，而是由老师以**压缩包**形式单独提供，你自己解压放到仓库根目录（这几个文件夹已 gitignore，不会污染仓库）：

* [**hydrodataset**](https://github.com/OuyangWenyu/hydrodataset/tree/feat/unified-data-path-resolution) — 数据路径解析底座
* [**hydrodatasource**](https://github.com/iHeadWater/hydrodatasource/tree/feat/unified-data-interface) — 自定义水文数据读取（本课程用 songliao 松辽数据）
* [**hydromodel**](https://gitcode.com/dlut-water/hydromodel/tree/refactor/remove-data-resolver-use-opendataset) — 概念性水文模型（XAJ 系列等）

再配合放入 `data/`（songliao 3h 洪水事件数据）。安装时这三份源码以 **editable** 方式装入环境，详见 [docs/setup.md](docs/setup.md)。

## 快速开始

```bash
# 1. 获取本仓库
cd ai\_hydro\_forecast\_homework

# 2. 放入老师给的源码与数据（压缩包解压到仓库根目录）
#    hydrodataset/  hydrodatasource/  hydromodel/  data/
#    详细步骤见 docs/setup.md

# 3. 创建虚拟环境（Python 必须 ≥3.11）
conda create -n hydro\_homework python=3.11
conda activate hydro\_homework

# 4. 从仓库根目录安装依赖（本地源码 editable + PyPI）
pip install -r requirements.txt

# 5. 启动 AI Agent（首次使用需先安装，见下方安装教程）
claude   # 或 opencode
```

> \*\*AI Agent 安装教程\*\*：
> - Claude Code 安装：\[docs/setup.md 第四步](docs/setup.md#第四步安装-ai-agent-工具)
> - 用 DeepSeek 低成本驱动 Claude Code（免订阅、国内直连）：\[docs/claude-code-deepseek.md](docs/claude-code-deepseek.md)

然后在 AI Agent 对话框里直接说：*"帮我率定 songliao 数据集，并把 NSE 报给我"*
（本仓库自带 songliao 率定 skill，见下方【内置 Skill】）

## 项目结构

```
ai\_hydro\_forecast\_homework/
├── README.md              # 本文件
├── CLAUDE.md              # AI Agent 项目说明（已 gitignore）
├── requirements.txt       # Python 依赖
├── .claude/
│   └── skills/
│       └── songliao-calibration/   # 内置 skill：率定+评估 songliao
├── docs/                  # 教程文档
│   ├── index.md           # 文档索引
│   ├── setup.md           # 环境搭建详解
│   ├── claude-code-deepseek.md  # 用 DeepSeek 低成本驱动 Claude Code
│   ├── prompt-tips.md     # Prompt 编写技巧
│   └── examples.md        # 操作示例
│
│   # 以下由你放入（压缩包解压），均已 gitignore：
├── hydrodataset/          # 源码
├── hydrodatasource/       # 源码
├── hydromodel/            # 源码（含 configs/songliao\_event\_3h.yaml）
└── data/                  # songliao 数据
```

## 内置 Skill：songliao 率定

本仓库自带一个 Claude Code skill：`.claude/skills/songliao-calibration/`。
在仓库里启动 Claude Code 后，直接用自然语言说需求即可，例如：

* *"帮我率定碧流河（songliao\_21401550），并把 NSE 报给我"*
* *"把模型换成 xaj、SCE-UA 的 rep 调到 8000 重跑"*
* *"调一下 kernel\_size 试试，看碧流河 NSE 有没有提升"*

Claude 会自动改 `hydromodel/configs/songliao\_event\_3h.yaml` 的参数、跑率定 + 评估、
读 `basins\_metrics.csv` 把 NSE / KGE / RMSE 等指标报给你。**改这份 yaml 的参数
（模型、迭代次数、kernel\_size、训练/测试时段）就能得到不同结果**——这正是本次作业的核心玩法。

## 作业任务

### 基础任务（必做）

|序号|任务|说明|
|-|-|-|
|1|环境搭建|配置 Python 环境，安装依赖，启动 AI Agent|
|2|数据加载|让 AI Agent 加载流域数据|
|3|模型选择|选择一个水文模型（songliao 是 3h 洪水事件数据，适配 XAJ 系列：xaj / xaj\_mz / semi\_xaj）|
|4|模型率定|配置并执行参数率定|
|5|结果评估|计算 NSE、KGE 等指标|
|6|可视化|生成降雨-径流过程图、散点图|

### 进阶任务（选做）

|序号|任务|说明|
|-|-|-|
|7|多模型对比|在碧流河流域上用 XAJ 系列各模型（xaj / xaj\_mz / semi\_xaj）分别率定，比较 NSE / KGE|
|8|参数调优|调 rep / ngs / kernel\_size 等，提升碧流河验证期 NSE，冲更高档次|
|9|敏感性分析|试不同 train/test 划分或 warmup，观察碧流河 NSE 的变化并在报告中分析|

### 提交内容

1. **对话记录**：AI Agent 对话历史导出
2. **结果文件**：率定参数、评估指标、图表
3. **实验报告**：工作流程、问题和心得（500 字内）

## 评价标准

总评由三部分构成，另设加分项。**率定质量不是唯一标准**——智能体的完善程度和实验报告同样重要。

|评分项|权重|说明|
|-|-|-|
|率定质量|40%|按**碧流河流域**验证期 NSE 水平分档，见下方【率定质量分档】|
|智能体完善程度|35%|对智能体的配置与改进质量（skill、soul.md 等）|
|实验报告|25%|工作流程、问题分析与心得|

### 率定质量分档

本作业只率定**碧流河流域**（basin id：`songliao\_21401550`）这一个流域，
按它在固定**验证期**内评估得到的 **NSE** 分档：

|档次|该项得分|碧流河验证期 NSE|
|-|-|-|
|**A**|90–100|≥ 0.70|
|**B**|80–89|0.55 \~ 0.70|
|**C**|70–79|0.40 \~ 0.55|
|**D**|60–69|0.20 \~ 0.40|
|**F**|< 60|< 0.20 / 无有效结果|

> - 同档内：NSE 越高、KGE 等其他指标越好，得分越高。
> - 验证期由 config 的 `test\_period` 固定——\*\*请勿修改验证期\*\*，训练/率定只用 `train\_period`。
> - 不要求率定其他流域；把碧流河这一个流域调好即可。

### 智能体完善程度

考察你对智能体本身的配置与打磨，不局限于某一个文件：

* **skill**：能按需求正确修改 config 参数（模型 / 迭代次数 / kernel\_size / 训练测试期）并跑通；对 songliao-calibration skill 的补充与改进（补排错说明、完善参数文档、支持新用法等）；触发准确、流程顺畅、结果汇报清晰
* **soul.md 等其他配置**：对智能体人设、行为准则、上下文（如 soul.md、CLAUDE.md、提示词等）的合理定制，让它更懂本任务
* 整体上智能体越"顺手好用"、越贴合 songliao 率定任务，得分越高

### 加分项（酌情加分）

在总评之上额外加分：

* 提交有价值的 **Issue**（报告 bug、提改进建议、复现并定位问题）
* 有意义的 **commit**（清晰改动 + 规范提交说明）
* 提交 **Pull Request**（修复或改进被采纳）

## 常见问题

**Q: AI Agent 生成的代码报错怎么办？**
A: 把错误信息贴给 AI Agent，让它诊断修复。学会 debug AI 写的代码是重要技能。

**Q: 能用 ChatGPT / Cursor 吗？**
A: 可以，任何支持项目级代码交互的 AI 工具都行。推荐 Claude Code。

**Q: 模型率定太慢？**
A: 先从短时间范围、少参数开始，跑通流程后再扩大。

**Q: 对水文模型完全不了解？**
A: 直接问 AI："什么是 NSE"、"XAJ 模型有哪些参数"。AI 既是工具也是老师。

\---

\## 常见问题 FAQ



\### Q1: 依赖安装报错怎么办？



确保使用 Python ≥ 3.11，按以下顺序安装：



```bash

pip install --upgrade pip setuptools wheel

pip install hatchling hatch-vcs editables

pip install -r requirements.txt --no-build-isolation

```



如果遇到 `PermissionError` 无法写入 `\_version.py`，请关闭占用该文件的程序（文件资源管理器、编辑器），或将项目移至 C 盘等非系统保护目录。



\### Q2: 数据路径验证返回 False



\- 确认 `data/` 文件夹下的目录名为 \*\*`songliaorrevent`\*\*（注意是两个 r，不是 songliaorevent）

\- 数据文件夹必须放在项目根目录（与 `hydromodel/` 文件夹同级）

\- 内部结构应为：`data/songliaorrevent/songliaorrevent/{attributes, shapes, timeseries}`



\### Q3: Claude Code 连不上 DeepSeek API



确保设置了以下 8 个环境变量（推荐通过 Windows 系统环境变量永久保存）：



| 变量名 | 值 |

|--------|-----|

| `ANTHROPIC\_BASE\_URL` | `https://api.deepseek.com/anthropic`（必须以 `/anthropic` 结尾） |

| `ANTHROPIC\_AUTH\_TOKEN` | 你的 DeepSeek API Key |

| `ANTHROPIC\_MODEL` | `deepseek-v4-pro` |

| `ANTHROPIC\_DEFAULT\_OPUS\_MODEL` | `deepseek-v4-pro` |

| `ANTHROPIC\_DEFAULT\_SONNET\_MODEL` | `deepseek-v4-pro` |

| `ANTHROPIC\_DEFAULT\_HAIKU\_MODEL` | `deepseek-v4-flash` |

| `CLAUDE\_CODE\_SUBAGENT\_MODEL` | `deepseek-v4-flash` |

| `CLAUDE\_CODE\_EFFORT\_LEVEL` | `max` |



临时设置（当前终端有效）：

```cmd

set ANTHROPIC\_BASE\_URL=https://api.deepseek.com/anthropic

set ANTHROPIC\_AUTH\_TOKEN=你的API\_Key

set ANTHROPIC\_MODEL=deepseek-v4-pro

...（其余变量同理）

```



\### Q4: scipy ftol 参数报 TypeError



YAML 会将 `1e-6` 这样的科学计数法解析为字符串而非浮点数。请将科学计数法改为十进制小数：



```yaml

\# ❌ 错误写法

ftol: 1e-6



\# ✅ 正确写法

ftol: 0.000001

```



\### Q5: semi\_xaj 模型无法运行



`semi\_xaj` 是半分布式新安江模型，需要子流域拓扑数据（`topo.txt`）和子单元属性文件（`attributes.nc`）才能运行。



\- 当前统一率定管线暂不支持 semi\_xaj

\- 请改用 \*\*`xaj`\*\*（标准新安江）或 \*\*`xaj\_mz`\*\*（优化汇流版，推荐）



\### Q6: xaj\_slw 模型 NSE 极低（甚至为负）



`xaj\_slw`（松辽加速版）有 26 个可调参数（将初始蓄水/流量状态也纳入了参数），高维参数空间在 5000-8000 次迭代下难以收敛。



\- 推荐使用 \*\*`xaj\_mz`\*\*（15 参数，本次实验最优 NSE=0.856）

\- 如果一定要用 xaj\_slw，建议大幅增加迭代次数（≥20000 次）



\---



\## xaj\_mz 模型 kernel\_size 参数推荐



基于碧流河流域的 19 组率定实验，`xaj\_mz` 的 `kernel\_size` 参数推荐值如下：



| kernel\_size | 单位线时长 | 推荐程度 | NSE（碧流河） |

|-------------|-----------|---------|--------------|

| 12 | 36h | ⭐⭐⭐ | 0.846 |

| 15 | 45h | ⭐⭐⭐⭐ | 0.852 |

| \*\*18\*\* | \*\*54h\*\* | \*\*⭐⭐⭐⭐⭐（甜点值）\*\* | \*\*0.856\*\* |

| 19 | 57h | ⭐⭐⭐⭐ | 0.852 |

| 21 | 63h | ⭐⭐⭐⭐ | 0.855 |



> 本项目使用 Gamma 分布参数化单位线（mizuRoute），kernel\_size \*\*奇偶数均可\*\*。



**联系人**: 张义猛 | **联系邮箱**: 2689874960@qq.com

