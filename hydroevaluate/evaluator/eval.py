"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 10:41:42
LastEditors: Wenyu Ouyang
LastEditTime: 2025-01-14 13:05:58
FilePath: \hydroevaluate\hydroevaluate\evaluator\eval.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

import warnings

import numpy as np
import pandas as pd


def read_rainfall_events_summary(csv_file_path):
    """
    读取降雨事件总结CSV文件，并返回一个字典，键为流域ID，值为事件列表。
    """
    summary_df = pd.read_csv(csv_file_path)
    events_dict = {}
    for index, row in summary_df.iterrows():
        basin = row["BASIN"]
        start_time = row["BEGINNING_RAIN"]
        end_time = row["END_RAIN"]
        if basin not in events_dict:
            events_dict[basin] = []
        events_dict[basin].append({"Start_Time": start_time, "End_Time": end_time})
    return events_dict


def cal_runoff_coefficient(xrds, prcp_col, flow_col):
    """calculate runoff coefficient

    First we check if precipitation and runoff are in the xrds, if not, we raise a warning and return None.

    Parameters
    ----------
    xrds : xr.Dataset
        input data
    """
    if prcp_col not in xrds:
        warnings.warn(
            "No precipitation data in the input xrds, please check the input data."
        )
        return None
    if flow_col not in xrds:
        warnings.warn(
            "No streamflow data in the input xrds, please check the input data."
        )
        return None
    flow_obs_values = xrds[flow_col].values
    precip_values = xrds[prcp_col].values
    valid_indices = ~np.isnan(flow_obs_values) & ~np.isnan(precip_values)
    flow_obs_coeff_total = (
        np.sum(flow_obs_values[valid_indices]) / np.sum(precip_values[valid_indices])
        if np.sum(precip_values[valid_indices]) != 0
        else np.nan
    )
    return flow_obs_coeff_total
