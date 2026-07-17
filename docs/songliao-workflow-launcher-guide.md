# Songliao 统一工作流入口

原始率定、评估和可视化脚本位于外置 `hydromodel/scripts/` 中，并依赖正确的
工作目录、Python 环境和配置路径。Windows 用户还容易混淆 PowerShell 与 cmd 的
`cd` 语法。`scripts/songliao_workflow.py` 在仓库根目录统一封装这些命令，不修改
hydromodel 的模型逻辑。

## 环境检查

```bash
python scripts/songliao_workflow.py doctor
```

`doctor` 检查数据目录、标准配置 `songliao_event_3h.yaml`、三个 hydromodel 脚本，
以及 `hydromodel`、`hydrodatasource`、`hydrodataset`、`hydroutils` 的可导入性。
自定义实验可使用 `--experiment EXPERIMENT_NAME`。

## 工作流命令

```bash
python scripts/songliao_workflow.py commands
python scripts/songliao_workflow.py calibrate --dry-run
python scripts/songliao_workflow.py evaluate
python scripts/songliao_workflow.py visualize --basin songliao_21401550
python scripts/songliao_workflow.py compare --basin songliao_21401550
```

`commands` 会按当前操作系统打印等价原始命令。`--dry-run` 只显示命令，不执行耗时
率定。真正运行 `calibrate` 前应确认配置、实验名和预计耗时。

## 改进价值

该入口把目录、解释器和编码等前置条件转化为可执行检查，降低“同一脚本在某终端
正常、在另一个终端报错”的复现风险，同时保留所有原始 hydromodel 命令。
