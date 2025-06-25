'''
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 10:41:42
LastEditors: zhuanglaihong
LastEditTime: 2025-06-24 15:48:19
FilePath: /zlh/hydroevaluate/tests/test_eval.py
Description:
'''
import os
import pytest
import numpy as np
import xarray as xr
import tempfile
import pandas as pd
import datetime

from hydroevaluate.evaluator.eval import (
    flood_event_split,
    flood_peak_bias,
    flood_peak_time_bias,
    flood_volume_bias,
    calculate_flood_forecast_qualification_rate
)


@pytest.fixture
def setup_eval_test_data(tmp_path):
    """
    创建用于评估函数测试的临时NC文件.
    包含两个洪水事件:
    1. 第一个事件是合格的.
    2. 第二个事件的洪峰误差不合格.
    """
    # 定义时间和流域维度
    times = pd.date_range("2024-01-01", periods=10, freq="D")
    basin_dim = 1

    # 创建观测流量数据 (m³/s)
    obs_flow = np.array([5, 8, 10, 20, 9, 7, 30, 40, 6, 4], dtype=np.float32)
    
    # 创建预报流量和洪水事件数据
    # 事件1 (合格): 洪峰=21(vs 20), 洪量=32(vs 30), 峰现时间一致
    # 事件2 (不合格): 洪峰=50(vs 40), 洪量=70(vs 70), 峰现时间差1天
    pred_flow = np.array([6, 9, 11, 21, 10, 8, 50, 20, 7, 5], dtype=np.float32)
    flood_event = np.array([0, 0, 0.5, 0.6, 0, 0, 0.7, 0.8, 0, 0], dtype=np.float32)

    # 创建观测nc文件
    obs_ds = xr.Dataset(
        {"inflow": (("time", "basin"), obs_flow.reshape(-1, 1))},
        coords={"time": times, "basin": np.arange(basin_dim)},
    )
    obs_nc_path = tmp_path / "obs.nc"
    obs_ds.to_netcdf(obs_nc_path)

    # 创建预报nc文件
    pred_ds = xr.Dataset(
        {
            "inflow": (("time", "basin"), pred_flow.reshape(-1, 1)),
            "flood_event": (("time", "basin"), flood_event.reshape(-1, 1)),
        },
        coords={"time": times, "basin": np.arange(basin_dim)},
    )
    pred_nc_path = tmp_path / "pred.nc"
    pred_ds.to_netcdf(pred_nc_path)

    # 返回文件路径和已知的时间点用于断言
    return str(pred_nc_path), str(obs_nc_path), times


def test_flood_peak_bias(setup_eval_test_data):
    pred_path, obs_path, times = setup_eval_test_data
    start_time = np.datetime64(times[2])
    end_time = np.datetime64(times[3])
    if hasattr(start_time, "to_datetime64"):
        start_time = start_time.to_datetime64()
    if hasattr(end_time, "to_datetime64"):
        end_time = end_time.to_datetime64()
    bias = flood_peak_bias(pred_path, obs_path, start_time=start_time, end_time=end_time)
    np.testing.assert_almost_equal(bias, 0.05, decimal=2)


def test_flood_volume_bias(setup_eval_test_data):
    pred_path, obs_path, times = setup_eval_test_data
    start_time = np.datetime64(times[2])
    end_time = np.datetime64(times[3])
    if hasattr(start_time, "to_datetime64"):
        start_time = start_time.to_datetime64()
    if hasattr(end_time, "to_datetime64"):
        end_time = end_time.to_datetime64()
    bias = flood_volume_bias(pred_path, obs_path, start_time=start_time, end_time=end_time)
    np.testing.assert_almost_equal(bias, 2/30, decimal=2)


def test_flood_peak_time_bias(setup_eval_test_data):
    pred_path, obs_path, times = setup_eval_test_data
    start_time = np.datetime64(times[6])
    end_time = np.datetime64(times[7])
    if hasattr(start_time, "to_datetime64"):
        start_time = start_time.to_datetime64()
    if hasattr(end_time, "to_datetime64"):
        end_time = end_time.to_datetime64()
    bias = flood_peak_time_bias(pred_path, obs_path, start_time=start_time, end_time=end_time)
    assert abs(bias) == 1.0


def test_calculate_flood_forecast_qualification_rate(setup_eval_test_data):
    pred_path, obs_path, times = setup_eval_test_data
    rate, df, _ = calculate_flood_forecast_qualification_rate(pred_path, obs_path, basin_index=0)
    assert rate == 50.0
