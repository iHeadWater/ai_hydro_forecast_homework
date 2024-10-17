"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2024-06-02 15:46:14
LastEditors: Wenyu Ouyang
Description: Load hydromodel
FilePath: \hydroevaluate\hydroevaluate\modelloader\model.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import json
import os
import numpy as np
import pandas as pd
import pint
from hydrodatasource.utils.utils import streamflow_unit_conv
from hydromodel.models.model_dict import MODEL_DICT
import torch
from torchhydro.models.model_dict_function import pytorch_model_dict
from torchhydro.models.model_utils import get_the_device

ALL_MODELS_DICT = {**MODEL_DICT, **pytorch_model_dict}


def load_hydromodel(model_cfgs):
    """
    Directly load the calibrated model with the given parameters
    one-time call for only one basin now
    """
    p_and_e = model_cfgs["p_and_e"]
    area = model_cfgs["area"]
    calibrated_norm_param_file = model_cfgs["calibrated_norm_param_file"]
    param_range_file = model_cfgs["param_range_file"]
    model_info_file = model_cfgs["model_info_file"]
    target_unit = model_cfgs["target_unit"]
    target_unit = "m^3/s" if target_unit is None else target_unit
    if not (p_and_e and area and calibrated_norm_param_file and param_range_file):
        raise ValueError(
            "p_and_e, area, calibrated_norm_param_file, param_range_file should be provided"
        )
    if model_info_file is None:
        model_info = {
            "name": "xaj",
            "source_book": "HF",
            "source_type": "sources5mm",
            "time_interval_hours": 3,
        }
    else:
        model_info = json.load(open(model_info_file, "r"))
    calibrated_norm_params = pd.read_csv(calibrated_norm_param_file, index_col=0).values
    return (
        p_and_e,
        area,
        calibrated_norm_params,
        param_range_file,
        model_info,
        target_unit,
    )


def load_torchmodel(model_cfgs):
    model_name = model_cfgs["model_name"]
    model_hyperparam = model_cfgs["model_hyperparam"]
    pth_path = model_cfgs["pth_path"]
    device_num = model_cfgs["device"]
    device = get_the_device(device_num)
    if model_name not in pytorch_model_dict.keys():
        raise ValueError(f"Unsupported model type: {model_name}")
    model = pytorch_model_dict[model_name](**model_hyperparam)
    model.load_state_dict(torch.load(pth_path, weights_only=True))
    model = model.to(device)
    return model


def infer_hydromodel(**kwargs):
    p_and_e = kwargs.get("p_and_e", None)
    area = kwargs.get("area", None)
    calibrated_norm_params = kwargs.get("calibrated_norm_params", None)
    param_range_file = kwargs.get("param_range_file", None)
    model_info = kwargs.get("model_info", None)
    target_unit = kwargs.get("target_unit", None)
    target_unit = "m^3/s" if target_unit is None else target_unit
    if not (p_and_e and area and calibrated_norm_params and param_range_file):
        raise ValueError(
            "p_and_e, area, calibrated_norm_params, param_range_file should be provided"
        )
    qsim, _ = MODEL_DICT[model_info["name"]](
        p_and_e,
        calibrated_norm_params,
        # we set the warmup_length=0 but later we get results from warmup_length to the end to evaluate
        warmup_length=0,
        **model_info,
        **{"param_range_file": param_range_file},
    )
    ureg = pint.UnitRegistry()
    ureg.force_ndarray_like = True
    q_sim_with_unit = qsim * ureg.mm / ureg.h / model_info["time_interval_hours"]
    area_np_with_unit = area * ureg.km**2
    return streamflow_unit_conv(q_sim_with_unit, area_np_with_unit, target_unit, True)


def infer_torchmodel(**kwargs):
    """The main difference between this function and the original infer_model from torchhydro
    is: this is a real case and only input is available, but no observation is available.

    Parameters
    ----------
    seq_first : _type_
        _description_
    device : _type_
        _description_
    model : _type_
        _description_
    xs : list or tensor
        xs is always batch first

    Returns
    -------
    _type_
        _description_
    """
    seq_first = kwargs.get("seq_first", False)
    model = kwargs.get("model", None)
    xs = kwargs.get("xs", None)
    device = kwargs.get("device", torch.device("cpu"))
    if model is None or xs is None:
        raise ValueError("model and xs should be provided")
    model = model.to(device)
    model.eval()
    if type(xs) is list:
        xs = [
            (
                data_tmp.permute([1, 0, 2]).to(device)
                if seq_first and data_tmp.ndim == 3
                else data_tmp.to(device)
            )
            for data_tmp in xs
        ]
    else:
        xs = [
            (
                xs.permute([1, 0, 2]).to(device)
                if seq_first and xs.ndim == 3
                else xs.to(device)
            )
        ]
    output = model(*xs)
    if type(output) is tuple:
        # Convention: y_p must be the first output of model
        output = output[0]
    if seq_first:
        output = output.transpose(0, 1)
    return output
