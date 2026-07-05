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
  hydrodataset/      # 你放入的源码（务必用 feat/unified-data-path-resolution 分支）
  hydrodatasource/   # 你放入的源码
  hydromodel/        # 你放入的源码
  data/              # 你放入的数据
  requirements.txt
```

> **hydrodataset 必须用 `feat/unified-data-path-resolution` 分支**：PyPI / main
> 版本缺少 `hydrodataset.configs` 模块、且会拉不兼容的 aqua_fetch，都会导致
> `import hydrodatasource` 失败。放入前先 `git checkout feat/unified-data-path-resolution`。

然后从仓库根目录安装依赖：

```bash
# 务必在仓库根目录执行，requirements.txt 里的 ./ 相对路径才能对上
cd ai_hydro_forecast_homework

# 三份本地源码以 editable 方式安装；mlflow / modelscope 走 PyPI
pip install -r requirements.txt
```

> **为什么用 editable（`-e ./...`）**：这样跑的是你放进来这份源码（含你的改动），
> 而不是 PyPI 上的发布版。
>
> **为什么要保留 `.git`**：`hydrodatasource` 用 hatch-vcs 从 git tag 推导版本，
> 若删掉 `.git`，安装会报"无法确定版本"而失败；`hydrodataset` 也要靠 `.git` 才能
> 停在正确的分支上。

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

## 第三步：配置数据访问

水文数据通常较大，我们通过以下方式访问：

### 方式一：远程数据源（推荐）

配置 MinIO 对象存储连接（助教会提供 access_key 和 secret）：

在用户目录创建 `~/hydro_setting.yml`：
```yaml
minio:
  server_url: 'http://minio.waterism.com:9090'
  client_endpoint: 'http://minio.waterism.com:9000'
  access_key: '你的access_key'
  secret: '你的secret'

local_data_path:
  root: 'D:/data/waterism'
  datasets-origin: 'D:/data/waterism/datasets-origin'
  datasets-interim: 'D:/data/waterism/datasets-interim'
```

### 方式二：本地数据

如果助教提供了数据文件，放到 `data/` 目录下，后续在 Prompt 中指定路径即可。

## 第四步：安装 AI Agent 工具

### Claude Code（推荐）

```bash
# 需要 Node.js >= 18
npm install -g @anthropic-ai/claude-code

# 启动（在项目目录下）
cd ai_hydro_forecast_homework
claude
```

首次启动需要：
1. 登录 Anthropic 账号
2. 配置 API Key 或通过 Claude 订阅使用

### OpenCode（备选）

```bash
pip install opencode

# 启动
cd ai_hydro_forecast_homework
opencode
```

## 第五步：验证全流程

启动 AI Agent 后，试试这个最简单的 Prompt：

> "你好，帮我检查一下当前环境，确认 hydromodel 和 hydrodatasource 都能正常 import"

如果 AI 回复正常，环境就搭好了！

## 常见问题

### Q: pip install 报错怎么办？
A: 把完整的错误信息贴给 AI Agent，让它帮你分析。通常是指定版本冲突或缺少系统依赖。

### Q: import 时报 `No module named 'hydrodataset.configs'` 或 `cannot import name 'check_attributes' from 'aqua_fetch.utils'`？
A: 两个都是**用错了 hydrodataset 版本**——你装的是 PyPI / main 版，它没有
`hydrodataset.configs` 模块、还会拉不兼容的 aqua_fetch。解决办法:把放入的
`hydrodataset/` 切到 **`feat/unified-data-path-resolution` 分支**，再重装:
```bash
cd hydrodataset
git checkout feat/unified-data-path-resolution
cd ..
python -m pip install -r requirements.txt
```
确认切对分支:`git -C hydrodataset branch --show-current`。

### Q: 提示 `Configuration file not found: ~/hydro_setting.yml`？
A: 这只是"没找到 MinIO 配置文件"的提示，不是致命错误，不影响本地数据（`data/`）的使用。
只有要用 MinIO 远程数据时才需要按上面"第三步 方式一"创建该文件。

### Q: Claude Code 连不上？
A: 检查网络（可能需要科学上网），确认 API Key 有效。

### Q: 数据连不上？
A: 确认 `~/hydro_setting.yml` 配置正确，access_key 和 secret 是否过期。
