"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2024-06-02 11:47:39
LastEditors: Wenyu Ouyang
Description: Test cases for EvalDeepHydro
FilePath: \hydroevaluate\tests\test_hydroevaluate.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from hydroevaluate.hydroevaluate import EvalDeepHydro
from hydroevaluate.configs.config import DEFAULT_cfgs


def test_load_config():
    eval_deep_hydro = EvalDeepHydro()
    assert "data_cfgs" in eval_deep_hydro.cfgs
    assert "model_cfgs" in eval_deep_hydro.cfgs
    assert "evaluation_cfgs" in eval_deep_hydro.cfgs


def test_model_infer():
    eval_deep_hydro = EvalDeepHydro(DEFAULT_cfgs)
    pred = eval_deep_hydro.model_infer()
    print(pred)
