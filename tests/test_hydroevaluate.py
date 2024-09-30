"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2024-06-02 11:47:39
LastEditors: Wenyu Ouyang
Description: Test cases for EvalDeepHydro
FilePath: \hydroevaluate\tests\test_hydroevaluate.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import os
from hydroevaluate.hydroevaluate import EvalDeepHydro
from hydroevaluate.configs.config import DEFAULT_cfgs


def test_load_config():
    eval_deep_hydro = EvalDeepHydro()
    assert "data_cfgs" in eval_deep_hydro.cfgs
    assert "model_cfgs" in eval_deep_hydro.cfgs
    assert "evaluation_cfgs" in eval_deep_hydro.cfgs


def test_model_infer():
    # TODO: put this if-else in an update-config function
    # sourcery skip: no-conditionals-in-tests
    if DEFAULT_cfgs["model_cfgs"]["download"]:
        DEFAULT_cfgs["model_cfgs"]["pth_path"] = os.path.join(
            DEFAULT_cfgs["model_cfgs"]["local_dir"],
            "best_model.pth",
        )
        DEFAULT_cfgs["data_cfgs"]["stat_file_path"] = os.path.join(
            DEFAULT_cfgs["model_cfgs"]["local_dir"],
            "dapengscaler_stat.json",
        )
    eval_deep_hydro = EvalDeepHydro(DEFAULT_cfgs)
    pred = eval_deep_hydro.model_infer()
    print(pred)
