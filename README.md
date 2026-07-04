# AI Hydro Forecast Homework

> 本科生实习课程：使用 AI Agent 工具辅助水文模型率定

## 关于本项目

本仓库不是代码库，而是一个 **AI Agent Skill 项目**——它提供文档、配置和教程，帮助学生用自然语言对话的方式，通过 Claude Code / OpenCode 等 AI Agent 工具调用水文模型，完成模型率定任务。

实际的水文模型代码由以下包提供（通过 `pip install` 安装）：
- [hydromodel](https://github.com/OuyangWenyu/hydromodel) — 概念性水文模型（XAJ、GR4J 等）
- [torchhydro](https://github.com/OuyangWenyu/torchhydro) — 深度学习水文模型
- [hydrodatasource](https://github.com/OuyangWenyu/hydrodatasource) — 水文数据源

## 快速开始

```bash
# 1. 克隆本项目
git clone <this-repo-url>
cd ai_hydro_forecast_homework

# 2. 创建虚拟环境
conda create -n hydro_homework python=3.10
conda activate hydro_homework

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 AI Agent
claude   # 或 opencode
```

然后在 AI Agent 对话框里直接说：*"帮我加载 CAMELS 数据，用 XAJ 模型做率定"*

## 项目结构

```
ai_hydro_forecast_homework/
├── README.md           # 本文件
├── CLAUDE.md           # AI Agent 配置模板（需自行创建，已 gitignore）
├── requirements.txt    # Python 依赖
└── docs/               # 教程文档
    ├── index.md        # 文档索引
    ├── setup.md        # 环境搭建详解
    ├── prompt-tips.md  # Prompt 编写技巧
    └── examples.md     # 操作示例
```

## 作业任务

### 基础任务（必做）

| 序号 | 任务 | 说明 |
|------|------|------|
| 1 | 环境搭建 | 配置 Python 环境，安装依赖，启动 AI Agent |
| 2 | 数据加载 | 让 AI Agent 加载流域数据 |
| 3 | 模型选择 | 选择并初始化一个水文模型（XAJ、GR4J、LSTM 等） |
| 4 | 模型率定 | 配置并执行参数率定 |
| 5 | 结果评估 | 计算 NSE、KGE 等指标 |
| 6 | 可视化 | 生成降雨-径流过程图、散点图 |

### 进阶任务（选做）

| 序号 | 任务 | 说明 |
|------|------|------|
| 7 | 多模型对比 | 率定 2+ 模型，对比性能 |
| 8 | 多流域测试 | 在 3+ 流域进行率定 |
| 9 | 滚动预报评估 | 模拟真实预报场景 |

### 提交内容

1. **对话记录**：AI Agent 对话历史导出
2. **结果文件**：率定参数、评估指标、图表
3. **实验报告**：工作流程、问题和心得（500 字内）

## 评价标准

| 评分项 | 权重 | 要求 |
|--------|------|------|
| 任务完成度 | 40% | 基础任务全部完成 |
| AI 交互质量 | 25% | Prompt 清晰有效，能主动发现和纠正问题 |
| 结果正确性 | 20% | 率定结果合理，评估计算正确 |
| 实验报告 | 15% | 有自己的思考和见解 |

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

**课程教师**: Wenyu Ouyang | **联系邮箱**: wenyuouyang@outlook.com
