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


def load_hydromodel(model_cfgs, **kwargs):
    """
    Directly load the calibrated model with the given parameters
    one-time call for only one basin now
    """
    gage_id = kwargs.get("gage_id", None)
    calibrated_norm_param_file = model_cfgs["json_folder"] + "/" + gage_id + ".json"
    param_range_file = model_cfgs["yaml_folder"] + "/" + gage_id + ".yaml"
    model = {
        "calibrated_norm_param_file": calibrated_norm_param_file,
        "param_range_file": param_range_file,
        "target_unit": None,
        "model_info_file": None,
    }
    model_json = json.load(open(calibrated_norm_param_file, "r"))
    # check parameters
    model["target_unit"] = (
        "m^3/s" if model["target_unit"] is None else model["target_unit"]
    )
    if model["model_info_file"] is None:
        model["model_info"] = {
            "name": "xaj",
            "source_book": "HF",
            "source_type": "sources5mm",
            "time_interval_hours": 3,
        }
    else:
        model["model_info"] = json.load(open(model["model_info_file"], "r"))
    df = pd.DataFrame(model_json["paraScopes"])
    df = df.set_index("key")
    df = df[["actualValue"]]
    filtered_df = df.T
    filtered_df["STCD"] = filtered_df.apply(lambda x: gage_id, axis=1)
    filtered_df = filtered_df.set_index("STCD")
    model["calibrated_norm_params"] = filtered_df.values
    return model


def load_torchmodel(model_cfgs):
    model_name = model_cfgs["model_name"]
    model_hyperparam = model_cfgs["model_hyperparam"]
    pth_path = model_cfgs["pth_path"]
    device_num = model_cfgs["device"]
    device = get_the_device(device_num)
    print("Using device:", device)
    if model_name not in pytorch_model_dict.keys():
        raise ValueError(f"Unsupported model type: {model_name}")
    model = pytorch_model_dict[model_name](**model_hyperparam)
    model.load_state_dict(torch.load(pth_path, map_location=device, weights_only=True))
    return model


def infer_hydromodel(p_and_e, model):
    calibrated_norm_params = model["calibrated_norm_params"]
    model_info = model["model_info"]
    param_range_file = model["param_range_file"]
    qsim, _ = MODEL_DICT[model_info["name"]](
        p_and_e,
        calibrated_norm_params,
        # we set the warmup_length=0 but later we get results from warmup_length to the end to evaluate
        warmup_length=0,
        **model_info,
        **{"param_range_file": param_range_file},
    )
    return qsim


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
