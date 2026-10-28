# 常见问题 FAQ

首次把环境跑通时最容易踩的坑都记在这里。语言和步骤与 [setup.md](setup.md) 保持一致。

**先跑环境自检（只读，不会改你的电脑）：**

```bash
# 任意系统，在仓库根目录、已激活的 Python 环境里：
python scripts/check_env.py
# 同样只读的另一写法：
python scripts/songliao_workflow.py doctor
```

Windows 也可以用 PowerShell 包装脚本（同样只检查、不改系统）：

```powershell
powershell -NoProfile -File scripts\check_env.ps1
```

自检会核对 Python 版本、本地源码是否放对、songliao 数据路径、hydromodel 脚本/配置、依赖能否 import、控制台编码、以及（若相关）GPU/CUDA。缺什么会打印对应的改法。

---

## 安装与 Python 环境

### Q: `pip install -r requirements.txt` 报 `editables` / `hatch-vcs` / `Unknown version source: vcs` / 写不了 `_version.py`？

老师提供的 `hydrodataset/`、`hydrodatasource/` 用 hatchling + hatch-vcs 做本地可编辑安装。pip 太旧、构建隔离环境缺包、或压缩包没有 git 元数据时，常见报错包括：

- `ModuleNotFoundError: No module named 'editables'`
- `Unknown version source: vcs`
- `PermissionError` 写不了 `_version.py`

请确认：

1. Python **≥ 3.11**（`python --version`）。3.10 会装不上 hydromodel。
2. 已经 `conda activate hydro_homework`。
3. 当前目录是**仓库根目录**（能看到 `requirements.txt`、`README.md`）。
4. 老师发的 `hydrodataset/`、`hydrodatasource/`、`hydromodel/` 已经解压到根目录。

然后按这个顺序装（先升级构建工具，再装本地包）：

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install hatchling hatch-vcs editables
python -m pip install -r requirements.txt --no-build-isolation
```

`requirements.txt` 里已经写了 hatchling / hatch-vcs / editables，新版本 pip 有时一步就能成功；若仍失败，用上面三步。

Windows 若是 `_version.py` 的 `PermissionError`：关掉占用该文件的资源管理器/编辑器预览，检查源码文件是否被标成只读，或把项目放到当前用户可写的目录后再装。**不要用本仓库的检测脚本去改文件属性**——它只报告问题。

### Q: import 时报 `No module named 'hydrodataset.configs'` 或 `cannot import name 'check_attributes'`？

装成了 **PyPI 上的 hydrodataset**，不是老师给的本地源码。PyPI 版没有 `hydrodataset.configs`，还会拉来不兼容的 aqua_fetch。

```bash
python -m pip show hydrodataset
# Location 应指向仓库里的 hydrodataset/ ，而不是 site-packages 里的发行版
python -m pip install -r requirements.txt
```

### Q: `ModuleNotFoundError: No module named 'hydroutils'`？尤其是在 PyCharm 里直接点运行？

几乎总是**用错了解释器**，或没在已激活的 `hydro_homework` 环境里安装依赖。

- 终端：先 `conda activate hydro_homework`，再 `python scripts/check_env.py` 看「当前解释器」是不是该环境里的 python。
- PyCharm：Settings → Python Interpreter，选 conda 环境 `hydro_homework` 的解释器，不要用 IDE 创建的 venv 或系统 Python。
- 运行 `hydromodel/scripts/*.py` 时，Working directory 必须是 **`hydromodel/`**，不是仓库根目录。配置里的 `uri: ../data/...` 是相对 `hydromodel/` 的。

PowerShell、cmd、Anaconda Prompt 都能跑，关键是**同一个 conda 环境 + 正确工作目录**。切目录语法不同，见下方「Windows」。

### Q: Python 版本要多少？必须用 conda 吗？

hydromodel 声明 `requires-python >= 3.11`，文档用 Miniconda + `hydro_homework` 是推荐路径，不是唯一路径。你可以用 venv/uv，但解释器必须 ≥ 3.11，并且从仓库根目录执行 `python -m pip install -r requirements.txt`。

---

## 数据与路径

### Q: 数据路径一直不对，目录名是 `songliaorevent` 还是 `songliaorrevent`？

正确名字是 **`songliaorrevent`（两个 r）**。少一个 r 会找不到数据。解压后必须是：

```
data/
└── songliaorrevent/
    └── songliaorrevent/      # 内层这一级才是数据根
        ├── attributes/       # 读取器强制需要
        ├── timeseries/       # 读取器强制需要
        └── shapes/           # 文档示例中有；没有时先看率定能否跑
```

它和 `hydromodel/` 一样，放在**仓库根目录**下。配置 `hydromodel/configs/songliao_event_3h.yaml` 里的 `uri` 应对准这个内层目录。相对写法（推荐）是：

```yaml
uri: ../data/songliaorrevent/songliaorrevent
```

相对路径是相对 **`hydromodel/`** 的，所以率定必须在 `hydromodel/` 里启动。

> **TODO（需老师确认）**：若本学期发放的压缩包解压后目录名与上面不一致，请在此注明实际文件夹名，避免学生按文档对不上。

### Q: 提示 `Configuration file not found: ~/hydro_setting.yml`？数据是不是没连上？

不是致命错误。本课程用本地 `data/`，**不需要** `~/hydro_setting.yml`。那是 MinIO 远程数据的配置。只有老师明确要求走远程桶时才需要它。

### Q: `FileNotFoundError: attributes.csv`？

多半是 hydrodatasource **版本不对**（旧版只认 csv 属性表）。请确认 `pip show hydrodatasource` 的 Location 指向仓库内的本地目录，再重装 `python -m pip install -r requirements.txt`。

### Q: `FileNotFoundError: ...\.cache\hydrodataset\...attributes.nc`？

新机器第一次跑、缓存目录还不存在。老师提供的 hydrodatasource 一般会自动建目录；若仍报错，说明不是带补丁的本地包。先重装本地源码。Windows 上若只想临时建目录（可选，不是检测脚本做的事）：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.cache\hydrodataset"
```

---

## Windows

### Q: 同一脚本在 Anaconda Prompt 能跑，在 PowerShell / PyCharm 里报错？

先跑 `python scripts/check_env.py`，对照「当前解释器」和「工作目录」。

切到仓库根目录：

| 终端 | 命令 |
|------|------|
| cmd / Anaconda Prompt | `cd /d C:\path\to\ai_hydro_forecast_homework` |
| PowerShell | `Set-Location -LiteralPath 'C:\path\to\ai_hydro_forecast_homework'` |

切到 hydromodel（跑率定/评估/画图）：

| 终端 | 命令 |
|------|------|
| cmd / Anaconda Prompt | `cd /d C:\path\to\ai_hydro_forecast_homework\hydromodel` |
| PowerShell | `Set-Location -LiteralPath 'C:\path\to\ai_hydro_forecast_homework\hydromodel'` |

然后：

```bash
python scripts/run_event_calibration.py --config configs/songliao_event_3h.yaml
```

不要在仓库根目录运行上述脚本。检测脚本可以用 `--commands-only` 把对应系统的命令再打印一遍。

### Q: 控制台中文乱码，或 emoji 触发 `UnicodeEncodeError`？

hydromodel 的打印里可能有 emoji，Windows 默认代码页不是 UTF-8 时会炸。

**当前窗口临时生效：**

```bat
REM cmd / Anaconda Prompt
set PYTHONUTF8=1
```

```powershell
$env:PYTHONUTF8="1"
```

然后重新运行脚本。检测脚本本身不会永久改你的系统代码页。

### Q: 解压后 pip 报权限错误，有人说要把项目从 D 盘挪到 C 盘？

常见原因是压缩包文件带只读属性、或当前用户对那个盘符/目录没有写权限。可以：

- 取消只读后重试；
- 把仓库放到你确实可写的目录。

不必认为「必须用 C 盘」——关键是**当前用户可写**。检测脚本若发现抽查文件不可写，会 WARN，但不会替你改属性。

### Q: 路径里有中文可以吗？

可以，但部分 Windows 工具和旧库会出乱码或找不到文件。若自检已经 WARN「路径含非 ASCII」，出问题时应把仓库移到纯英文路径再试。

### Q: 需要 GPU / CUDA 吗？

**不需要。** 本课程是概念性 XAJ + SCE-UA，在 CPU 上跑。没有 NVIDIA 驱动、没有 CUDA、没有 PyTorch，都不影响完成作业。检测脚本会报告 GPU 情况，缺 GPU 不会判 FAIL。

---

## AI Agent（Claude Code / DeepSeek）

### Q: Claude Code 连不上 DeepSeek，模型不识别？

不要只设一两个变量。用 DeepSeek 驱动 Claude Code 时，请按 [claude-code-deepseek.md](claude-code-deepseek.md) 配齐变量，尤其是：

- `ANTHROPIC_BASE_URL` 必须是 `https://api.deepseek.com/anthropic`（**末尾 `/anthropic` 不能少**）
- `ANTHROPIC_AUTH_TOKEN` 填 DeepSeek API Key，**不要带 `<>`**，不要提交到 git
- 模型名不要随手写；以 `docs/claude-code-deepseek.md` 为准（文档示例是 `deepseek-v4-pro[1m]` / `deepseek-v4-flash` 这一组）

环境变量若只在当前终端 `set` / `$env:...`，关掉窗口就没了。永久配置见该文档文末（系统环境变量或 `~/.claude/settings.json` 的 `env` 字段）。

> **TODO（需老师确认）**：若本学期课程统一指定了与 `docs/claude-code-deepseek.md` 不同的模型名或网关地址，请更新那份文档，并在此留一句「以课程群通知为准」。

### Q: `claude` 命令找不到？Node 要多高版本？

Claude Code 需要 **Node.js ≥ 18**。先 `node -v`，再：

```bash
npm install -g @anthropic-ai/claude-code
```

若仍找不到命令：确认 npm 全局 bin 在 PATH 里，然后**新开**一个终端。安装步骤见 [setup.md 第四步](setup.md#第四步安装-ai-agent-工具)。

### Q: 能用 ChatGPT / Cursor 吗？

可以。任何能在本项目目录里改文件、跑命令的 AI 工具都行。仓库自带的 skill 是给 Claude Code 用的；换工具时请自己把 `.claude/skills/songliao-calibration/SKILL.md` 的流程读给它。

---

## 率定、模型与结果

### Q: 率定跑完了，为什么只有 RMSE，没有 NSE？

率定目标函数是 RMSE。**NSE 要再跑评估**才会出现在
`hydromodel/results/songliao_event/songliao_event_3h/evaluation_test/basins_metrics.csv`。

```bash
cd hydromodel
python scripts/run_xaj_evaluate.py --calibration-dir results/songliao_event/songliao_event_3h --eval-period test
```

### Q: 换成 GR4J / LSTM 跑不通？

songliao 是 **3h 洪水事件**数据，适配 XAJ 系列（`xaj` / `xaj_mz` / `xaj_slw`）。GR 系列是日/月尺度；评估脚本也是 XAJ 专用。作业任务里的多模型对比是在 XAJ 系列内部换。

### Q: `semi_xaj` 一跑就报拓扑 / 子流域文件错误？

有同学反馈 `semi_xaj` 需要 `topo.txt` 等拓扑数据，而当前统一数据包里没有；相关实现里也有「尚未完成」的注释。**当前更稳妥的选择是 `xaj` 或 `xaj_mz`（文档默认）。**

> **TODO（需老师确认）**：`semi_xaj` 本学期是否仍列为可选模型？若作业不支持，请在 README 的模型列表里划掉或加「暂不可用」；若已经可用，请注明还需要哪些额外文件。

### Q: scipy 的 `ftol: 1e-6` 报 TypeError？

YAML 有时会把 `1e-6` 解析成字符串。课程默认优化器是 **SCE-UA**，一般碰不到这个问题。若你自己改成 scipy L-BFGS-B，请写成十进制小数：

```yaml
ftol: 0.000001    # 不要写 1e-6
```

### Q: 模型率定太慢？

SCE-UA 的 `rep` 越大越慢。先把流程跑通（小 `rep`，例如几百到一千）再加大。正式率定文档建议 5000+。不要靠 GPU 加速——这个优化器走 CPU。

### Q: 对水文模型完全不了解？

直接问 AI：「什么是 NSE」「XAJ 有哪些参数」。把报错原文贴回去让它修，是本课程要练的技能。

---

## 作业要求（只重复仓库里已写明的部分）

评分、分档、提交物以 [README.md](../README.md) 为准，这里不另编截止日期或给分细则。

已经写在 README 里、需要特别留心的两点：

- 本作业率定**碧流河**（`songliao_21401550`）。
- 验证期由配置的 `test_period` 固定——**请勿修改验证期**；训练只用 `train_period`。

> **TODO（需老师确认）**：提交方式、命名、截止时间若只在课堂/群里通知、仓库未写，请不要让学生到 FAQ 里找；有书面规定后再补到 README。

遇到文档解决不了的问题：把 `python scripts/check_env.py` 的全文和报错贴给 AI，或联系 README 末尾的老师邮箱。

---

## 检测脚本做了什么、没做什么

| 会做 | 不会做 |
|------|--------|
| 读 Python 版本、解释器路径、conda 环境名 | 创建/删除 conda 环境 |
| 检查源码目录、数据目录、配置 uri、脚本是否存在 | 改 yaml、改数据、改只读属性 |
| 尝试 import 已安装的包 | `pip install` / 升级包 |
| 报告 GPU、Node、DeepSeek 相关环境变量是否存在 | 写入用户或系统环境变量 |
| 按操作系统打印该怎么 `cd`、该跑哪条命令 | 真正开始率定或评估 |

密钥类变量（如 `ANTHROPIC_AUTH_TOKEN`）只显示「已设置/未设置」，**不会打印密钥内容**。
