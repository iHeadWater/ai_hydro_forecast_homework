'''
Author: zhuanglaihong
Date: 2025-06-24 16:42:48
LastEditTime: 2025-06-25 15:16:22
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

def plot_flood_event(
    pred_nc_file,
    obs_nc_file,
    output_path,
    data_path,
    start_time,
    end_time,
    basin_name,
    flow_var="inflow",
    time_unit="1D",
    title=None,
):
    """
    绘制一个流域单场洪水事件的预报与观测流量过程线，并叠加降雨过程线。

    参数:
    ----------
    pred_nc_file : str
        包含预报数据的nc文件路径。
    obs_nc_file : str
        包含观测数据的nc文件路径。
    output_path : str
        生成的图像文件的完整保存路径 (包括文件名, e.g., 'output/event_1.png')。
    data_path : str
        Hydro格式的数据集路径。
    start_time : str or datetime
        洪水事件的开始时间。
    end_time : str or datetime
        洪水事件的结束时间。
    basin_name : str
        流域名称.
    flow_var : str, optional
        nc文件中代表流量的变量名称，默认为 'inflow'。
    time_unit : str
        时间单位。
    title : str, optional
        图像的标题。默认为 None，将自动生成标题。

    返回:
    -------
    None
        此函数没有返回值，但会将生成的图像以png格式保存到指定的 `output_path`。
    """
    load_user_font()

    # 读取数据
    pred_ds = xr.open_dataset(pred_nc_file)
    obs_ds = xr.open_dataset(obs_nc_file)

    dataset = SelfMadeHydroDataset(
        data_path=data_path,
        time_unit=[time_unit],
        offset_to_utc=True,  # 必须加，不加为空值
    )

    # 筛选时间和流域
    pred_event_ds = pred_ds.sel(time=slice(start_time, end_time), basin=basin_name)
    obs_event_ds = obs_ds.sel(time=slice(start_time, end_time), basin=basin_name)

    time_coords = obs_event_ds["time"].values
    pred_flow = pred_event_ds[flow_var].values
    obs_flow = obs_event_ds[flow_var].values

    # 读取降雨数据（假设变量名为rain，且为mm单位）
    precip_data = dataset.read_timeseries(
        object_ids=[basin_name],
        t_range_list=[start_time, end_time],
        relevant_cols=["rain"],
    )
    # 获取降雨序列
    precip = precip_data[time_unit][0, :, 0]  # [流域索引, 时间, 变量索引]

    if title is None:
        title = f"Flood Event: {pd.to_datetime(start_time).strftime('%Y-%m-%d')} to {pd.to_datetime(end_time).strftime('%Y-%m-%d')}"

    # 检查输出目录是否存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Plot rainfall-runoff comparison figure
    plot_rainfall_runoff(
        time_coords,
        precip,
        [obs_flow, pred_flow],
        fig_size=(10, 6),
        title=title,
        ylabel=f"{flow_var}(m^3/s)",
        prcp_ylabel="Precipitation (mm)",
        leg_lst=["observed flow", "predicted flow"],
    )

    plt.savefig(output_path)
    plt.close()