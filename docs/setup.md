# 环境搭建详解

## 前置要求

- 一台能上网的电脑（Windows / macOS / Linux 均可）
- 基本的命令行使用能力（会 `cd`、`ls` 就行）
- 一个 API Key（用于 AI Agent 调用大模型）

## 第一步：安装 Python 环境

推荐使用 Miniconda 管理 Python 环境：

> 注意：Python 版本要 **3.11 或更高**。hydromodel 要求 `requires-python >=3.11`，
> 用 3.10 会装不上。

**Windows:**
```bash
# 下载并安装 Miniconda: https://docs.conda.io/en/latest/miniconda.html
# 安装后打开 Anaconda Prompt（或终端）
conda create -n hydro_homework python=3.11
conda activate hydro_homework
```

**macOS / Linux:**
```bash
# 安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建环境
conda create -n hydro_homework python=3.11
conda activate hydro_homework
```

## 第二步：放入源码并安装依赖

本仓库**不自带** `hydrodataset/`、`hydrodatasource/`、`hydromodel/`、`data/`，
需要你自己把这几份放到仓库根目录下（它们已在 `.gitignore` 中，不会污染本仓库）：

```
ai_hydro_forecast_homework/
  hydrodataset/      # 你放入的源码
  hydrodatasource/   # 你放入的源码
  hydromodel/        # 你放入的源码
  data/              # 你放入的数据
  requirements.txt
```

然后从仓库根目录安装依赖：

```bash
# 务必在仓库根目录执行，requirements.txt 里的 ./ 相对路径才能对上
cd ai_hydro_forecast_homework

# 三份本地源码以 editable 方式安装；mlflow / modelscope 走 PyPI
pip install -r requirements.txt
```

验证安装（确认用的是本地源码）：
```bash
python -c "import hydromodel, hydrodatasource; print('imports OK')"

# 确认装的是仓库里的本地源码，而不是 PyPI 版：
# Windows:
pip show hydrodatasource | findstr Location
# macOS / Linux:
# pip show hydrodatasource | grep Location
```
`Location` 应指向仓库里的 `hydrodatasource` 目录。

## 第三步：数据放置

本课程用**本地数据**：老师会把 songliao 数据以压缩包形式提供，你在第二步已把它解压到
仓库根目录的 `data/`。解压后目录结构应是：

```
data/
└── songliaorrevent/
    └── songliaorrevent/      # 内层这一级才是数据根
        ├── attributes/
        ├── shapes/
        └── timeseries/
```

率定配置 `hydromodel/configs/songliao_event_3h.yaml` 里已用相对路径
`uri: ../data/songliaorrevent/songliaorrevent` 指向它（相对 `hydromodel/` 目录）。

## 第四步：安装 AI Agent 工具

### Claude Code

```bash
# 需要 Node.js >= 18
npm install -g @anthropic-ai/claude-code

# 启动（在项目目录下）
cd ai_hydro_forecast_homework
claude
```

## 第五步：验证全流程

启动 AI Agent 后，试试这个最简单的 Prompt：

> "你好，帮我检查一下当前环境，确认 hydromodel 和 hydrodatasource 都能正常 import"

如果 AI 回复正常，环境就搭好了！

## 常见问题

### Q: pip install 报错怎么办？
A: 把完整的错误信息贴给 AI Agent，让它帮你分析。通常是指定版本冲突或缺少系统依赖。

### Q: import 时报 `No module named 'hydrodataset.configs'` 或 `cannot import name 'check_attributes' from 'aqua_fetch.utils'`？
A: 两个都是**用错了 hydrodataset**——你装的是 PyPI 版，它没有 `hydrodataset.configs`
模块、还会拉不兼容的 aqua_fetch。解决办法:确认放入的 `hydrodataset/` 是老师提供的
源码（不是 PyPI 版），再重装:
```bash
python -m pip install -r requirements.txt
```

### Q: 提示 `Configuration file not found: ~/hydro_setting.yml`？
A: 这只是"没找到 MinIO 配置文件"的提示，不是致命错误，不影响本地数据（`data/`）的使用。
只有要用 MinIO 远程数据时才需要按上面"第三步 方式一"创建该文件。

### Q: Claude Code 连不上？
A: 检查网络（可能需要科学上网），确认 API Key 有效。

### Q: 数据连不上？
A: 确认 `~/hydro_setting.yml` 配置正确，access_key 和 secret 是否过期。
