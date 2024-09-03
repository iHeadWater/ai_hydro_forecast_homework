'''
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 10:16:32
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-03 15:35:17
FilePath: /hydroevaluate/hydroevaluate/configs/config.py
Description:
'''
DEFAULT_CONFIG = {
    "data_config":{
        "data_dir": "",
        "basin_ids": [],
        "data_names": [],
        "data_units": [],  
    },
    "model_config":{
        "model_type": "hydromodel",
        "p_and_e": [],
        "area": 1000, # str
        "calibrated_norm_param_file": None,
        "param_range_file": None,
        "model_info_file": None,
        "target_unit": "m^3/s",
    }
}