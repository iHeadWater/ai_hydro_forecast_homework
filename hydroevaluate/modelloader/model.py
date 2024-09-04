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

ALL_MODELS_DICT = {**MODEL_DICT, **pytorch_model_dict}


def load_hydromodel(config):
    """
    Directly load the calibrated model with the given parameters
    one-time call for only one basin now
    """
    p_and_e = config["model_config"]["p_and_e"]
    area = config["model_config"]["area"]
    calibrated_norm_param_file = config["model_config"]["calibrated_norm_param_file"]
    param_range_file = config["model_config"]["param_range_file"]
    model_info_file = config["model_config"]["model_info_file"]
    target_unit = config["model_config"]["target_unit"]
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


def load_torchmodel(model_config):
    model_name = model_config["model_name"]
    model_hyperparam = model_config["model_hyperparam"]
    pth_path = model_config["pth_path"]
    if model_name not in pytorch_model_dict.keys():
        raise ValueError(f"Unsupported model type: {model_name}")
    model = pytorch_model_dict[model_name](**model_hyperparam)
    model.load_state_dict(torch.load(pth_path))
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
    device = kwargs.get("device", "cpu")
    model = kwargs.get("model", model)
    xs = kwargs.get("xs", xs)
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


def _read_history_model(user_model_type, version, history_dict_path):
    # TODO: maybe under case like same model different version will be used
    result = {}
    models = os.listdir(os.path.join(work_dir, "test_data/models"))
    # 姑且假设model的名字为wasted_v1.pth，即用途_版本.pth
    current_max = 0
    for model_name in models:
        if user_model_type in model_name:
            model_ver = int(model_name.split(".")[0].split("v")[1])
            if model_ver > current_max:
                current_max = model_ver
    model_file_name = f"{user_model_type}_v{str(version)}.pth"
    if model_file_name in models:
        result[user_model_type] = current_max
        np.save(history_dict_path, result, allow_pickle=True)
    return result
