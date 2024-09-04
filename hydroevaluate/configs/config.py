"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 10:16:32
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-04 11:01:45
FilePath: /hydroevaluate/hydroevaluate/cfgs/cfg.py
Description:
"""

DEFAULT_cfg = {
    "data_cfg": {
        "data_dir": "",
        "stat_file_path": "",
        "basin_ids": [],
        "data_units": [],
        "var_lst": [],
        "constant_vars": [],
    },
    "model_cfg": {
        "model_type": "hydromodel",
        "p_and_e": [],
        "area": 1000,
        "calibrated_norm_param_file": None,
        "param_range_file": None,
        "model_info_file": None,
        "target_unit": "m^3/s",
    },
    "evaluation_cfg": {
        "seq_first": True,
    },
}
