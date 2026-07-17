# Songliao 提交前自检

`scripts/check_songliao_submission.py` 在不重跑率定的情况下核验配置、率定 JSON、
评估指标、反归一化参数、散点图和洪水事件图。默认检查标准实验
`songliao_event_3h` 与流域 `songliao_21401550`。

## 基本用法

```bash
python scripts/check_songliao_submission.py
python scripts/check_songliao_submission.py \
  --experiment songliao_event_3h_rep8000 \
  --nse-threshold 0.55
```

FDC 默认是建议项；需要将它作为必交项时增加 `--require-fdc`。洪水过程图最少数量
可通过 `--min-flood-events` 调整。

## 检查自定义报告与 PR 材料

工具不猜测学生姓名或报告文件名。使用可重复参数显式指定：

```bash
python scripts/check_songliao_submission.py \
  --report path/to/report.docx \
  --pr-file path/to/pr-description.md
```

`[OK]` 表示满足要求，`[WARN]` 表示建议项缺失，`[FAIL]` 表示核心输出或明确要求的
文件缺失。任一失败项会返回非零退出码，便于 Agent 或自动化流程判断提交状态。
