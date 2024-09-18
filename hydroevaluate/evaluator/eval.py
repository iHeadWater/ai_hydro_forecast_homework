"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 10:41:42
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-18 11:54:00
FilePath: /hydroevaluate/hydroevaluate/evaluator/eval.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

import warnings
from hydroevaluate.dataloader.common import GPM, GFS, SMAP
import yaml
from hydroevaluate.utils.heutils import (
    gee_gpm_to_1h_data,
    calculate_nse,
    plot_time_series,
    gee_gfs_tp_data_process,
)
from hydroevaluate.modelloader.model import load_hydromodel, load_torchmodel
import os


class Evaluator:
    def __init__(self, cfgs):
        self.data_dir = cfgs["data_dir"]
        self.object_ids = cfgs["object_ids"]
        interval = cfgs["min_time_interval"]
        unit = cfgs["min_time_unit"]
        time_unit = f"{interval}{unit}"
        self.time_unit = time_unit
        self.data_reader = cfgs["data_reader"]
        self.model_type = cfgs["model_type"]  # hydromodel or torchhydro

    def load_model(self, **kwargs):
        pass
