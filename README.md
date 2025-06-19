<!--
 * @Author: Wenyu Ouyang
 * @Date: 2023-10-29 17:35:04
 * @LastEditTime: 2025-06-19 16:38:40
 * @LastEditors: Wenyu Ouyang
 * @Description: Hydro forecast
 * @FilePath: \hydroevaluate\README.md
 * Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
-->
# hydroevaluate

hydroevaluate is a Python toolkit specifically designed to provide forecasting evaluation capabilities for hydrological models. This project aims to provide a more practical evaluation framework for trained hydrological models through inference computation and comprehensive evaluation analysis.

## Project Background

Current issues with hydrological model evaluation:
- Both physically-based and machine learning-based hydrological models primarily rely on existing datasets for offline evaluation without considering actual forecasting scenarios
- Lack of comprehensive assessment for hydrological forecasting performance
- Tedious and time-consuming work such as plotting requires significant effort

HydroEvaluate addresses these issues by providing a unified evaluation framework to facilitate the evaluation and comparison of hydrological models.

## Main Features

### 1. Model Inference Computation
- **Multi-model Support**: Seamless integration with torchhydro and hydromodel packages
- **Weight Loading**: Support for loading trained model weight files
- **Data Processing**: Utilize mature data reading modules with automatic normalization and denormalization
- **Inference Prediction**: Perform inference computation

### 2. Evaluation Analysis
- **Metric Calculation**: Provide comprehensive hydrological evaluation metrics (NSE, KGE, etc.)
- **Visualization Analysis**: Generate professional hydrological charts and comparative analysis plots
- **Pipeline Configuration**: Flexibly specify evaluation metrics and visualization content through configuration files
- **Report Generation**: Automatically generate evaluation reports

### 3. Data Pipeline
- **Multi-source Data Support**: Support for CAMELS, ERA5-Land, NLDAS, and other data sources
- **Time Series Processing**: Time series data loader specifically designed for hydrological forecasting
- **Forecast Scenario Simulation**: Simulate data input methods under real forecasting conditions

## Installation

### Requirements
- Python >= 3.10
- PyTorch
- Other dependencies listed in requirements.txt

### Installation Methods

```bash
# Install from PyPI
pip install hydroevaluate

# Or install from source
git clone https://github.com/OuyangWenyu/hydroevaluate.git
cd hydroevaluate
pip install -e .
```

## Quick Start

### Basic Usage Workflow

**TODO: Complete usage workflow**

1. **Prepare Configuration File**
```python
from hydroevaluate import HydroEvaluate
import yaml

# Load configuration file
with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
```

2. **Initialize Evaluator**
```python
# For deep learning models
evaluator = EvalDeepHydro(config)

# For physical hydrological models
evaluator = EvalHydroModel(config)
```

3. **Execute Inference and Evaluation**
```python
# Model inference
predictions = evaluator.model_infer()

# Model evaluation
eval_results = evaluator.model_evaluate(observations)
```

### Configuration File Structure

The configuration file contains three main sections:

```yaml
# Data configuration
data_cfgs:
  source_cfgs:
    source_name: "camels_us"
    source_path: "/path/to/data"
  object_ids: ["basin_001", "basin_002"]
  t_range_test: [["2019-06-01", "2019-10-01"]]
  relevant_cols: ["total_precipitation_hourly", "sm_surface"]
  target_cols: ["streamflow"]

# Model configuration
model_cfgs:
  model_type: "torchhydro"  # or "hydromodel"
  model_name: "Seq2Seq"
  pth_path: "/path/to/model.pth"
  device: [0]

# Evaluation configuration
evaluation_cfgs:
  metrics: ["NSE", "KGE", "RMSE"]
  rolling: 56
  seq_first: false
```

## Project Architecture

```
hydroevaluate/
├── configs/          # Configuration management
├── dataloader/       # Data loading modules
├── modelloader/      # Model loading modules
├── evaluator/        # Evaluation computation modules
├── reporter/         # Report generation modules
└── utils/           # Utility functions
```

### Core Module Description

- **ModelLoader**: Unified model loading interface supporting torchhydro and hydromodel
- **HydroDataLoader**: Hydrological data loader for handling time series data
- **Evaluator**: Evaluation module including metric calculation and visualization functions
- **Reporter**: Report generation and result output module

## Supported Model Types

### Deep Learning Models (TorchHydro)
- Seq2Seq LSTM
- Transformer
- CNN-LSTM
- Other PyTorch-implemented hydrological models

### Physical Hydrological Models (HydroModel)
- Xinanjiang Model (XAJ)
- GR4J Model
- Other conceptual hydrological models

## Supported Data Sources

- **CAMELS**: Continental-scale basin dataset of the United States
- **ERA5-Land**: European Centre for Medium-Range Weather Forecasts land surface reanalysis data
- **NLDAS**: North American Land Data Assimilation System
- **MODIS**: Satellite remote sensing soil moisture and evapotranspiration data
- **Custom Data Sources**: Support for user-defined data formats

## Evaluation Metrics

### Hydrology-specific Metrics
- **NSE**: Nash-Sutcliffe Efficiency coefficient
- **KGE**: Kling-Gupta Efficiency coefficient
- **RMSE**: Root Mean Square Error
- **MAE**: Mean Absolute Error
- **Runoff Coefficient**: Water balance analysis

### Visualization Features
- Rainfall-runoff process plots
- Model prediction vs observation comparison plots
- Error distribution plots
- Time series analysis plots

## Advanced Features

### Rolling Forecast Evaluation
Support for simulating rolling forecast evaluation under real forecasting scenarios:
```python
# Configure rolling forecast parameters
evaluation_cfgs = {
    "rolling": 56,  # Perform forecast every 56 time steps
    "forecast_length": 56,  # Forecast length
    "hindcast_length": 240  # Historical data length
}
```

### Batch Basin Evaluation
Support for batch evaluation and comparative analysis of multiple basins:
```python
object_ids = ["basin_001", "basin_002", "basin_003"]
# Automatically process multiple basins in a loop
```

### Model Performance Comparison
Support for historical evaluation result comparison and performance trend analysis:
```python
# Generate comparison report
evaluator.compare_history_report(new_eval_log, old_eval_log)
```

## Development Roadmap

- [ ] Add more evaluation metrics
- [ ] Support more data sources
- [ ] Enhance visualization capabilities
- [ ] Add model uncertainty analysis
- [ ] Develop web interface
- [ ] Support distributed computing

## Contributing

All forms of contributions are welcome! Please refer to [CONTRIBUTING.md](contributing.md) for detailed information.

## License

This project uses the BSD license. See [LICENSE](LICENSE) file for details.

## Contact

- **Project Homepage**: https://github.com/OuyangWenyu/hydroevaluate
- **Documentation**: https://hydroevaluate.readthedocs.io/
- **Issue Reporting**: https://github.com/OuyangWenyu/hydroevaluate/issues

## Citation

If you use HydroEvaluate in your research, please cite:

```bibtex
@software{hydroevaluate,
  title={HydroEvaluate: A Real Evaluation Tool for Hydrological Forecast},
  author={Wenyu Ouyang},
  url={https://github.com/OuyangWenyu/hydroevaluate},
  year={2024}
}
```

---

**Note**: This project is under active development and APIs may change. It is recommended to follow project updates and check the changelog.
