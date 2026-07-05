# 用 DeepSeek 官方方案配置 Claude Code

> 整理自组内语雀《AI 编程 Agent 命令行工具使用简介》中的「deepseek 官方配置方案」一节，
> 并补全了原文只给了链接、未列出的环境变量（取自 DeepSeek 官方文档最新值）。
>
> 官方参考：[接入 Agent 工具 | DeepSeek API Docs](https://api-docs.deepseek.com/zh-cn/guides/coding_agents)

这套方案不需要 Anthropic 付费订阅，用 DeepSeek 的 API Key 直接驱动 Claude Code，
成本低、国内可直连，适合本课程的日常使用。

## 第一步：安装 Node.js

Claude Code 依赖 Node.js（要求 **18+**）。

1. 到官网下载对应系统的安装包：[Node.js — 下载](https://nodejs.org/zh-cn/download/)
2. 一路 next 安装完成
3. 新开一个终端，确认安装成功并查看版本：

```bash
node -v
npm -v
```

## 第二步：（可选）安装 Git

官方教程提到需要 Git，但实测**不是必须的** —— 没有 Git 也能装 Claude Code。

- **macOS**：一般自带，无需处理
- **Windows**：如确实需要 Git，到 [Git for Windows](https://git-scm.com/install/windows) 下载，一路 next；
  装完新开终端 `git -v` 能输出版本即成功

## 第三步：安装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

## 第四步：获取 DeepSeek API Key

1. 打开 [DeepSeek 开放平台](https://www.deepseek.com/)，进入「API 开放平台」
2. 左侧选择「API keys」→「创建 API key」
3. **复制并妥善保存**（key 只显示一次）

## 第五步：配置环境变量

以下变量把 Claude Code 的接口指向 DeepSeek。**注意**：官方给的是「临时」配置，
只在**当前终端窗口**生效，关掉就失效（想永久生效见文末提示）。

**Windows（PowerShell）：**
```powershell
$env:ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
$env:ANTHROPIC_AUTH_TOKEN="<你的 DeepSeek API Key>"
$env:ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
$env:ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
$env:CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
$env:CLAUDE_CODE_EFFORT_LEVEL="max"
```

**macOS / Linux（bash / zsh）：**
```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<你的 DeepSeek API Key>
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max
```

> 配置要点：
> - base_url 末尾的 `/anthropic` 不能少 —— 它让 Claude Code 走 DeepSeek 的 Anthropic 兼容接口。
> - 填 key 时**不要带 `<>`**，引号内直接就是 key 本身。
> - 模型名（`deepseek-v4-pro` / `deepseek-v4-flash`）可能随 DeepSeek 更新，以官方文档为准。

## 第六步：启动并验证

在任意项目目录启动：

```bash
cd 你的项目目录
claude
```

首次进入会有一些配置界面，一路 Enter 即可。进去后用 `/status` 确认当前模型是 DeepSeek，
再随便对话一句确保能正常响应，即配置完成。

---

## 提示：让环境变量永久生效

第五步是临时配置，每次新开终端都要重设。想一劳永逸，二选一：

- **写进 shell 配置**：macOS/Linux 把 `export ...` 那几行追加到 `~/.zshrc` 或 `~/.bashrc`；
  Windows 用「系统属性 → 环境变量」加为用户变量。
- **写进 Claude Code 配置文件**：编辑 `~/.claude/settings.json`，放到 `env` 字段里，例如：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "你的DeepSeek_API_Key",
    "ANTHROPIC_MODEL": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash"
  }
}
```

> ⚠️ API Key 是明文，别把含 key 的 `settings.json` 或 shell 配置提交到 git、也别外发。

## 常见问题

**Q：`claude` 命令找不到？**
A：确认第三步 `npm install -g` 成功，且 npm 全局 bin 目录在 PATH 里；重开终端再试。

**Q：`/status` 显示的还是 Anthropic 官方模型？**
A：环境变量没生效 —— 检查是否在**同一个**终端窗口设置并启动，或改用 `settings.json` 永久配置。

**Q：报鉴权/401 错误？**
A：多半是 API Key 错误或带了 `<>`；重新核对第四步的 key，注意别有多余空格。
