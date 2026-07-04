# 环境搭建详解

## 前置要求

- 一台能上网的电脑（Windows / macOS / Linux 均可）
- 基本的命令行使用能力（会 `cd`、`ls` 就行）
- 一个 API Key（用于 AI Agent 调用大模型）

## 第一步：安装 Python 环境

推荐使用 Miniconda 管理 Python 环境：

**Windows:**
```bash
# 下载并安装 Miniconda: https://docs.conda.io/en/latest/miniconda.html
# 安装后打开 Anaconda Prompt（或终端）
conda create -n hydro_homework python=3.10
conda activate hydro_homework
```

**macOS / Linux:**
```bash
# 安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建环境
conda create -n hydro_homework python=3.10
conda activate hydro_homework
```

## 第二步：安装依赖包

```bash
# 进入项目目录
cd ai_hydro_forecast_homework

# 安装水文模型相关依赖
pip install -r requirements.txt
```

验证安装：
```bash
python -c "import hydromodel; print('hydromodel OK')"
python -c "import torchhydro; print('torchhydro OK')"
python -c "import hydrodatasource; print('hydrodatasource OK')"
```

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

> "你好，帮我检查一下当前环境，确认 hydromodel 和 torchhydro 都能正常 import"

如果 AI 回复正常，环境就搭好了！

## 常见问题

### Q: pip install 报错怎么办？
A: 把完整的错误信息贴给 AI Agent，让它帮你分析。通常是指定版本冲突或缺少系统依赖。

### Q: Claude Code 连不上？
A: 检查网络（可能需要科学上网），确认 API Key 有效。

### Q: 数据连不上？
A: 确认 `~/hydro_setting.yml` 配置正确，access_key 和 secret 是否过期。
