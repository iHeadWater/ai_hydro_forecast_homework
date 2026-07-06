# AI Hydro Forecast Homework

> 本科生实习课程：使用 AI Agent 工具辅助水文模型率定

## 关于本项目

本仓库不是代码库，而是一个 **AI Agent Skill 项目**——它提供文档、配置和教程，帮助学生用自然语言对话的方式，通过 Claude Code / OpenCode 等 AI Agent 工具调用水文模型，完成模型率定任务。

实际的水文模型代码**不随本仓库分发**，而是由老师以**压缩包**形式单独提供，你自己解压放到仓库根目录（这几个文件夹已 gitignore，不会污染仓库）：
- **hydrodataset** — 数据路径解析底座
- **hydrodatasource** — 自定义水文数据读取（本课程用 songliao 松辽数据）
- **hydromodel** — 概念性水文模型（XAJ 系列等）

再配合放入 `data/`（songliao 3h 洪水事件数据）。安装时这三份源码以 **editable** 方式装入环境，详见 [docs/setup.md](docs/setup.md)。

## 快速开始

```bash
# 1. 获取本仓库
cd ai_hydro_forecast_homework

# 2. 放入老师给的源码与数据（压缩包解压到仓库根目录）
#    hydrodataset/  hydrodatasource/  hydromodel/  data/
#    详细步骤见 docs/setup.md

# 3. 创建虚拟环境（Python 必须 ≥3.11）
conda create -n hydro_homework python=3.11
conda activate hydro_homework

# 4. 从仓库根目录安装依赖（本地源码 editable + PyPI）
pip install -r requirements.txt

# 5. 启动 AI Agent（首次使用需先安装，见下方安装教程）
claude   # 或 opencode
```

> **AI Agent 安装教程**：
> - Claude Code 安装：[docs/setup.md 第四步](docs/setup.md#第四步安装-ai-agent-工具)
> - 用 DeepSeek 低成本驱动 Claude Code（免订阅、国内直连）：[docs/claude-code-deepseek.md](docs/claude-code-deepseek.md)

然后在 AI Agent 对话框里直接说：*"帮我率定 songliao 数据集，并把 NSE 报给我"*
（本仓库自带 songliao 率定 skill，见下方【内置 Skill】）

## 项目结构

```
ai_hydro_forecast_homework/
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
├── hydromodel/            # 源码（含 configs/songliao_event_3h.yaml）
└── data/                  # songliao 数据
```

## 内置 Skill：songliao 率定

本仓库自带一个 Claude Code skill：`.claude/skills/songliao-calibration/`。
在仓库里启动 Claude Code 后，直接用自然语言说需求即可，例如：

- *"帮我率定碧流河（songliao_21401550），并把 NSE 报给我"*
- *"把模型换成 xaj、SCE-UA 的 rep 调到 8000 重跑"*
- *"调一下 kernel_size 试试，看碧流河 NSE 有没有提升"*

Claude 会自动改 `hydromodel/configs/songliao_event_3h.yaml` 的参数、跑率定 + 评估、
读 `basins_metrics.csv` 把 NSE / KGE / RMSE 等指标报给你。**改这份 yaml 的参数
（模型、迭代次数、kernel_size、训练/测试时段）就能得到不同结果**——这正是本次作业的核心玩法。

## 作业任务

### 基础任务（必做）

| 序号 | 任务 | 说明 |
|------|------|------|
| 1 | 环境搭建 | 配置 Python 环境，安装依赖，启动 AI Agent |
| 2 | 数据加载 | 让 AI Agent 加载流域数据 |
| 3 | 模型选择 | 选择一个水文模型（songliao 是 3h 洪水事件数据，适配 XAJ 系列：xaj / xaj_mz / semi_xaj） |
| 4 | 模型率定 | 配置并执行参数率定 |
| 5 | 结果评估 | 计算 NSE、KGE 等指标 |
| 6 | 可视化 | 生成降雨-径流过程图、散点图 |

### 进阶任务（选做）

| 序号 | 任务 | 说明 |
|------|------|------|
| 7 | 多模型对比 | 在碧流河流域上用 XAJ 系列各模型（xaj / xaj_mz / semi_xaj）分别率定，比较 NSE / KGE |
| 8 | 参数调优 | 调 rep / ngs / kernel_size 等，提升碧流河验证期 NSE，冲更高档次 |
| 9 | 敏感性分析 | 试不同 train/test 划分或 warmup，观察碧流河 NSE 的变化并在报告中分析 |

### 提交内容

1. **对话记录**：AI Agent 对话历史导出
2. **结果文件**：率定参数、评估指标、图表
3. **实验报告**：工作流程、问题和心得（500 字内）

## 评价标准

总评由三部分构成，另设加分项。**率定质量不是唯一标准**——智能体的完善程度和实验报告同样重要。

| 评分项 | 权重 | 说明 |
|--------|------|------|
| 率定质量 | 40% | 按**碧流河流域**验证期 NSE 水平分档，见下方【率定质量分档】 |
| 智能体完善程度 | 35% | 对智能体的配置与改进质量（skill、soul.md 等） |
| 实验报告 | 25% | 工作流程、问题分析与心得 |

### 率定质量分档

本作业只率定**碧流河流域**（basin id：`songliao_21401550`）这一个流域，
按它在固定**验证期**内评估得到的 **NSE** 分档：

| 档次 | 该项得分 | 碧流河验证期 NSE |
|------|----------|-----------------|
| **A** | 90–100 | ≥ 0.70 |
| **B** | 80–89 | 0.55 ~ 0.70 |
| **C** | 70–79 | 0.40 ~ 0.55 |
| **D** | 60–69 | 0.20 ~ 0.40 |
| **F** | < 60 | < 0.20 / 无有效结果 |

> - 同档内：NSE 越高、KGE 等其他指标越好，得分越高。
> - 验证期由 config 的 `test_period` 固定——**请勿修改验证期**，训练/率定只用 `train_period`。
> - 不要求率定其他流域；把碧流河这一个流域调好即可。

### 智能体完善程度

考察你对智能体本身的配置与打磨，不局限于某一个文件：

- **skill**：能按需求正确修改 config 参数（模型 / 迭代次数 / kernel_size / 训练测试期）并跑通；对 songliao-calibration skill 的补充与改进（补排错说明、完善参数文档、支持新用法等）；触发准确、流程顺畅、结果汇报清晰
- **soul.md 等其他配置**：对智能体人设、行为准则、上下文（如 soul.md、CLAUDE.md、提示词等）的合理定制，让它更懂本任务
- 整体上智能体越"顺手好用"、越贴合 songliao 率定任务，得分越高

### 加分项（酌情加分）

在总评之上额外加分：

- 提交有价值的 **Issue**（报告 bug、提改进建议、复现并定位问题）
- 有意义的 **commit**（清晰改动 + 规范提交说明）
- 提交 **Pull Request**（修复或改进被采纳）

## 常见问题

**Q: AI Agent 生成的代码报错怎么办？**
A: 把错误信息贴给 AI Agent，让它诊断修复。学会 debug AI 写的代码是重要技能。

**Q: 能用 ChatGPT / Cursor 吗？**
A: 可以，任何支持项目级代码交互的 AI 工具都行。推荐 Claude Code。

**Q: 模型率定太慢？**
A: 先从短时间范围、少参数开始，跑通流程后再扩大。

**Q: 对水文模型完全不了解？**
A: 直接问 AI："什么是 NSE"、"XAJ 模型有哪些参数"。AI 既是工具也是老师。

---

**联系人**: 张义猛 | **联系邮箱**: 2689874960@qq.com
