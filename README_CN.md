<!--
 * @Author: Wenyu Ouyang
 * @Date: 2024-02-12 09:52:49
 * @LastEditTime: 2025-06-19 16:33:54
 * @LastEditors: Wenyu Ouyang
 * @Description: 中文版README
 * @FilePath: \hydroevaluate\README_CN.md
 * Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
-->
# hydroevaluate

hydroevaluate 是一个专为水文模型提供预报评估能力的Python工具包。该项目旨在通过推理计算和全面的评估分析，为已训练的水文模型提供更贴近实际应用场景的评估框架。

## 项目背景

现阶段水文模型评估存在的问题：
- 无论是基于物理机制还是机器学习的水文模型，主要都依托于现成的数据集进行离线评估，没考虑实际预报场景
- 缺乏针对水文预报性能的衡量不够全面
- 画图等繁琐工作工作量较大

HydroEvaluate就是针对上述问题，提供一个统一的评估框架，以便于对水文模型进行评估和比较。

## 主要功能

### 1. 模型推理计算
- **多模型支持**：无缝集成torchhydro和hydromodel两大水文建模包
- **权重加载**：支持加载已训练完成的模型权重文件
- **数据处理**：利用成熟的数据读取模块，自动处理数据归一化和反归一化
- **推理预测**：进行推理计算

### 2. 评估分析
- **指标计算**：提供丰富的水文评估指标（NSE、KGE等）
- **可视化分析**：生成专业的水文图表和对比分析图
- **流水线配置**：通过配置文件灵活指定评估指标和可视化内容
- **报告生成**：自动生成评估报告

### 3. 数据管道
- **多源数据支持**：支持CAMELS、ERA5-Land、NLDAS等多种数据源
- **时间序列处理**：专为水文预报设计的时间序列数据加载器
- **预报场景模拟**：模拟真实预报条件下的数据输入方式

## 安装

### 环境要求
- Python >= 3.10
- PyTorch
- 其他依赖详见requirements.txt

### 安装方式

```bash
# 从PyPI安装
pip install hydroevaluate

# 或者从源码安装
git clone https://github.com/OuyangWenyu/hydroevaluate.git
cd hydroevaluate
pip install -e .
```

## 快速开始

### 基本使用流程

**TODO: 补充使用流程**

1. **准备配置文件**
```python
from hydroevaluate import HydroEvaluate
import yaml

# 加载配置文件
with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
```

2. **初始化评估器**
```python
# 对于深度学习模型
evaluator = EvalDeepHydro(config)

# 对于物理水文模型
evaluator = EvalHydroModel(config)
```

3. **执行推理和评估**
```python
# 模型推理
predictions = evaluator.model_infer()

# 模型评估
eval_results = evaluator.model_evaluate(observations)
```

### 配置文件结构

配置文件包含三个主要部分：

```yaml
# 数据配置
data_cfgs:
  source_cfgs:
    source_name: "camels_us"
    source_path: "/path/to/data"
  object_ids: ["basin_001", "basin_002"]
  t_range_test: [["2019-06-01", "2019-10-01"]]
  relevant_cols: ["total_precipitation_hourly", "sm_surface"]
  target_cols: ["streamflow"]

# 模型配置
model_cfgs:
  model_type: "torchhydro"  # 或 "hydromodel"
  model_name: "Seq2Seq"
  pth_path: "/path/to/model.pth"
  device: [0]

# 评估配置
evaluation_cfgs:
  metrics: ["NSE", "KGE", "RMSE"]
  rolling: 56
  seq_first: false
```

## 项目架构

```
hydroevaluate/
├── configs/          # 配置管理
├── dataloader/       # 数据加载模块
├── modelloader/      # 模型加载模块
├── evaluator/        # 评估计算模块
├── reporter/         # 报告生成模块
└── utils/           # 工具函数
```

### 核心模块说明

- **ModelLoader**: 统一的模型加载接口，支持torchhydro和hydromodel
- **HydroDataLoader**: 水文数据加载器，处理时间序列数据
- **Evaluator**: 评估模块，包含指标计算和可视化功能
- **Reporter**: 报告生成和结果输出模块

## 支持的模型类型

### 深度学习模型 (TorchHydro)
- Seq2Seq LSTM
- Transformer
- CNN-LSTM
- 其他PyTorch实现的水文模型

### 物理水文模型 (HydroModel)
- 新安江模型 (XAJ)
- GR4J模型
- 其他概念性水文模型

## 支持的数据源

- **CAMELS**: 美国大陆规模流域数据集
- **ERA5-Land**: 欧洲中期天气预报中心陆面再分析数据
- **NLDAS**: 北美陆面数据同化系统
- **MODIS**: 卫星遥感土壤湿度和蒸散发数据
- **自定义数据源**: 支持用户自定义数据格式

## 评估指标

### 水文专用指标
- **NSE**: Nash-Sutcliffe效率系数
- **KGE**: Kling-Gupta效率系数
- **RMSE**: 均方根误差
- **MAE**: 平均绝对误差
- **径流系数**: 水量平衡分析

### 可视化功能
- 降雨-径流过程图
- 模型预测vs观测对比图
- 误差分布图
- 时间序列分析图

## 高级功能

### 滚动预报评估
支持模拟真实预报场景下的滚动预报评估：
```python
# 配置滚动预报参数
evaluation_cfgs = {
    "rolling": 56,  # 每56个时间步进行一次预报
    "forecast_length": 56,  # 预报长度
    "hindcast_length": 240  # 历史数据长度
}
```

### 批量流域评估
支持多个流域的批量评估和对比分析：
```python
object_ids = ["basin_001", "basin_002", "basin_003"]
# 自动循环处理多个流域
```

### 模型性能对比
支持历史评估结果对比和性能趋势分析：
```python
# 生成对比报告
evaluator.compare_history_report(new_eval_log, old_eval_log)
```

## 开发计划

- [ ] 增加更多评估指标
- [ ] 支持更多数据源
- [ ] 增强可视化功能
- [ ] 添加模型不确定性分析
- [ ] 开发Web界面
- [ ] 支持分布式计算

## 贡献指南

欢迎各种形式的贡献！请参考[CONTRIBUTING.md](contributing.md)了解详细信息。

## 许可证

本项目使用BSD许可证。详见[LICENSE](LICENSE)文件。

## 联系方式

- **项目主页**: https://github.com/OuyangWenyu/hydroevaluate
- **文档**: https://hydroevaluate.readthedocs.io/
- **问题反馈**: https://github.com/OuyangWenyu/hydroevaluate/issues

## 引用

如果您在研究中使用了HydroEvaluate，请引用：

```bibtex
@software{hydroevaluate,
  title={HydroEvaluate: A Real Evaluation Tool for Hydrological Forecast},
  author={Wenyu Ouyang},
  url={https://github.com/OuyangWenyu/hydroevaluate},
  year={2024}
}
```

---

**注意**: 该项目正在积极开发中，API可能会发生变化。建议关注项目更新并查看更新日志。
