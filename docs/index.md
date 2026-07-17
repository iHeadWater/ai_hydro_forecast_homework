# 文档索引

欢迎！这里是你完成水文模型率定作业所需的一切教程。

## 文档列表

| 文档 | 内容 |
|------|------|
| [环境搭建详解](setup.md) | Python 环境配置、依赖安装、AI Agent 工具安装 |
| [用 DeepSeek 配置 Claude Code](claude-code-deepseek.md) | 免订阅、低成本驱动 Claude Code 的官方配置方案 |
| [Prompt 编写技巧](prompt-tips.md) | 如何写出高效的 Prompt，让 AI 更懂你的需求 |
| [操作示例](examples.md) | 从零到率定的完整对话示例 |
| [统一工作流入口](songliao-workflow-launcher-guide.md) | 从仓库根目录检查并运行 Songliao 流程 |
| [多实验结果对比](songliao-experiment-comparison-guide.md) | 自动汇总调参实验并按 NSE 排名 |
| [提交前自检](songliao-submission-audit-guide.md) | 不重跑模型地检查指标、参数和图件 |

## 学习路径建议

```
环境搭建 → 看懂示例 → 自己写 Prompt → 完成基础任务 → 挑战进阶任务
```

1. **先搭环境**：按 [setup.md](setup.md) 一步步来，确保 `claude` 能正常启动
2. **照猫画虎**：看 [examples.md](examples.md) 里的对话示例，复制类似的 Prompt
3. **独立操作**：按你的需求写好 Prompt，引导 AI 完成每个步骤
4. **进阶挑战**：XAJ 系列内多模型对比、覆盖更多流域、调参提升 NSE

> 💡 本仓库自带 **songliao-calibration** skill：启动 Claude Code 后直接说
> "帮我率定 songliao" 即可，它会自动改 `songliao_event_3h.yaml`、跑率定+评估、报指标。

## 遇到问题？

- 先把错误信息贴给 AI Agent，让它帮你诊断
- 查看 [Prompt 编写技巧](prompt-tips.md) 的"常见翻车现场"章节
- 实在解决不了，问老师和助教
