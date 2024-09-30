"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 09:50:27
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-04 16:10:20
FilePath: /hydroevaluate/tests/test_dataloader.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

import pytest
from hydroevaluate.configs.config import DEFAULT_cfgs
from hydroevaluate.dataloader.data_processor import DapengScalerForEval
from hydrodatasource.reader.data_source import SelfMadeHydroDataset


@pytest.fixture
def default_config():
    config = DEFAULT_cfgs
    data_source = SelfMadeHydroDataset(config["data_cfgs"]["data_dir"])
    scaler = DapengScalerForEval(
        relevant_vars=config["data_cfgs"]["var_lst"],
        constant_vars=config["data_cfgs"]["constant_vars"],
        data_cfgs=config["data_cfgs"],
        data_source=data_source,
    )
    return config, scaler


def test_read_mean_prcp(default_config):
    _, scaler = default_config
    mean_prcp = scaler.mean_prcp
    print(mean_prcp)
