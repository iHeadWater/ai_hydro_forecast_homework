'''
Author: zhuanglaihong
Date: 2025-06-24 16:42:48
LastEditTime: 2025-06-24 19:36:27
LastEditors: zhuanglaihong
Description: 
FilePath: /zlh/hydroevaluate/tests/test_plt.py
Copyright: Copyright (c) 2021-2024 zhuanglaihong. All rights reserved.
'''
import os
import numpy as np
import pandas as pd
import xarray as xr
import pytest

from hydroevaluate.evaluator.plt import plot_flood_event

@pytest.fixture
def setup_plot_test_data(tmp_path):
    # 生成简单的测试nc文件
    times = pd.date_range("2024-01-01", periods=5, freq="D")
    basin_dim = 1
    obs_flow = np.array([5, 8, 10, 20, 9], dtype=np.float32)
    pred_flow = np.array([6, 9, 11, 21, 10], dtype=np.float32)
    flood_event = np.array([0, 0.5, 0.6, 0, 0], dtype=np.float32)
    precip = np.array([0, 2, 5, 1, 0], dtype=np.float32)

    obs_ds = xr.Dataset(
        {
            "inflow": (("time", "basin"), obs_flow.reshape(-1, 1)),
            "precip": (("time", "basin"), precip.reshape(-1, 1)),
        },
        coords={"time": times, "basin": np.arange(basin_dim)},
    )
    obs_nc_path = tmp_path / "obs.nc"
    obs_ds.to_netcdf(obs_nc_path)

    pred_ds = xr.Dataset(
        {
            "inflow": (("time", "basin"), pred_flow.reshape(-1, 1)),
            "flood_event": (("time", "basin"), flood_event.reshape(-1, 1)),
        },
        coords={"time": times, "basin": np.arange(basin_dim)},
    )
    pred_nc_path = tmp_path / "pred.nc"
    pred_ds.to_netcdf(pred_nc_path)

    return str(pred_nc_path), str(obs_nc_path), times

def test_plot_flood_event(tmp_path, setup_plot_test_data):
    pred_path, obs_path, times = setup_plot_test_data
    output_path = tmp_path / "flood_event_test.png"
    # 调用绘图函数
    plot_flood_event(
        pred_nc_file=pred_path,
        obs_nc_file=obs_path,
        output_path=str(output_path),
        start_time=times[1],
        end_time=times[3],
        basin_index=0,
        flow_var="inflow",
        precip_var=None,
        title="Test Flood Event"
    )
    # 检查图片文件是否生成
    assert os.path.exists(output_path)
    # 检查文件大小大于0
    assert os.path.getsize(output_path) > 0
