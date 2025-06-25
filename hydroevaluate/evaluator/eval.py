"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 10:41:42
LastEditors: zhuanglaihong
LastEditTime: 2025-06-24 16:05:58
FilePath: \hydroevaluate\hydroevaluate\evaluator\eval.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

import warnings
import numpy as np
import pandas as pd
import xarray as xr

from hydroevaluate.evaluator.plt import  plot_predobs_with_tp_hydro


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


def flood_event_split(
    nc_file_path,
    basin_name,
    threshold=0.01,
    flood_var="flood_event",
    time_var="time",
):
    """
    划分洪水场次，返回每个场次的起始和终止时间（datetime格式）。
    参数：
        nc_file_path: nc文件路径
        basin_name: 选择的流域名称（字符串，需与nc文件中的basin坐标一致）
        threshold: 判定洪水的阈值
        flood_var: 洪水事件变量名
        time_var: 时间变量名
    返回：
        flood_periods: list，每场洪水的(起始时间, 终止时间)元组，均为datetime类型
    """
    ds = xr.open_dataset(nc_file_path)
    # 直接用流域名索引
    flood = ds[flood_var].sel(basin=basin_name).values
    times = ds[time_var].values
    times_dt = pd.to_datetime(times)
    flood_periods = []
    in_flood = False
    start_time = None
    end_time = None
    for i in range(len(flood)):
        if flood[i] > threshold:
            if not in_flood:
                start_time = times_dt[i]
                in_flood = True
            end_time = times_dt[i]  # 每次大于阈值都更新end_time
        elif in_flood:
            # 洪水区间结束，记录start和end
            flood_periods.append((start_time, end_time))
            in_flood = False
    # 如果最后一直是洪水状态，补充终止时间为最后一个大于阈值的时间
    if in_flood:
        flood_periods.append((start_time, end_time))
    return flood_periods


def flood_peak_bias(
    pred_nc_file_path,
    obs_nc_file_path,
    basin_name,
    flow_var="inflow",
    start_time=None,
    end_time=None,
):
    """
    计算单场洪水的洪峰偏差（预报洪水最大流量与实测值的相对误差）。
    参数：
        pred_nc_file_path: 预报nc文件路径
        obs_nc_file_path: 实测nc文件路径
        basin_name: 选择的流域名称（字符串，需与nc文件中的basin坐标一致）
        flow_var: 流量变量名（预报和实测一致）
        start_time: 分析的起始时间（必须指定）
        end_time: 分析的终止时间（必须指定）
    返回：
        peak_bias: 单场洪水的洪峰偏差（相对误差）
    """
    time_var = "time"
    ds_pred = xr.open_dataset(pred_nc_file_path)
    ds_obs = xr.open_dataset(obs_nc_file_path)
    times = ds_pred[time_var].values
    flow_pred = ds_pred[flow_var].sel(basin=basin_name).values
    flow_obs = ds_obs[flow_var].sel(basin=basin_name).values

    if start_time is None or end_time is None:
        raise ValueError("请输入start_time和end_time用于单场洪水分析。")

    mask = (times >= start_time) & (times <= end_time)
    if not np.any(mask):
        return np.nan

    pred_peak = np.max(flow_pred[mask])
    obs_peak = np.max(flow_obs[mask])
    return np.nan if obs_peak == 0 else (pred_peak - obs_peak) / obs_peak


def flood_peak_time_bias(
    pred_nc_file,
    obs_nc_file,
    basin_name,
    flow_var="inflow",
    start_time=None,
    end_time=None,
):
    """
    计算单场洪水预报峰现时间偏差。
    参数：
        pred_nc_file: 预报nc文件路径
        obs_nc_file: 实测nc文件路径
        basin_name: 选择的流域名称（字符串，需与nc文件中的basin坐标一致）
        flow_var: 流量变量名
        start_time: 洪水开始时间（必须指定）
        end_time: 洪水结束时间（必须指定）
    返回：
        peak_time_bias: 预报洪峰出现时间与实测洪峰出现时间的差值（单位：天，若为小时数据则为小时）
    """
    time_var = "time"
    if start_time is None or end_time is None:
        raise ValueError("请指定start_time和end_time用于单场洪水分析。")
    pred_ds = xr.open_dataset(pred_nc_file)
    obs_ds = xr.open_dataset(obs_nc_file)
    times = pred_ds[time_var].values
    pred_flow = pred_ds[flow_var].sel(basin=basin_name).values
    obs_flow = obs_ds[flow_var].sel(basin=basin_name).values
    mask = (times >= start_time) & (times <= end_time)
    if not np.any(mask):
        return np.nan
    # 只取区间内数据
    times_sel = times[mask]
    pred_flow_sel = pred_flow[mask]
    obs_flow_sel = obs_flow[mask]
    # 洪峰索引
    pred_peak_idx = np.argmax(pred_flow_sel)
    obs_peak_idx = np.argmax(obs_flow_sel)
    pred_peak_time = times_sel[pred_peak_idx]
    obs_peak_time = times_sel[obs_peak_idx]
    return (pred_peak_time - obs_peak_time) / np.timedelta64(1, "D")


def flood_volume_bias(
    pred_nc_file,
    obs_nc_file,
    basin_name,
    flow_var="inflow",
    start_time=None,
    end_time=None,
):
    """
    计算单场洪水的洪量误差（预报和实测分别为两个nc文件，变量名相同）。
    参数：
        pred_nc_file: 预报nc文件路径
        obs_nc_file: 实测nc文件路径
        basin_name: 选择的流域名称（字符串，需与nc文件中的basin坐标一致）
        flow_var: 流量变量名
        start_time: 洪水开始时间（必须指定）
        end_time: 洪水结束时间（必须指定）
    返回：
        volume_bias: 单场洪水的洪量误差（相对误差）
    """
    time_var = "time"
    if start_time is None or end_time is None:
        raise ValueError("请指定start_time和end_time用于单场洪水分析。")
    pred_ds = xr.open_dataset(pred_nc_file)
    obs_ds = xr.open_dataset(obs_nc_file)
    times = pred_ds[time_var].values
    pred_flow = pred_ds[flow_var].sel(basin=basin_name).values
    obs_flow = obs_ds[flow_var].sel(basin=basin_name).values
    mask = (times >= start_time) & (times <= end_time)
    if not np.any(mask):
        return np.nan
    pred_volume = np.sum(pred_flow[mask])
    obs_volume = np.sum(obs_flow[mask])
    if obs_volume == 0:
        return np.nan
    return (pred_volume - obs_volume) / obs_volume


def calculate_flood_forecast_qualification_rate(
    pred_nc_file,
    obs_nc_file,
    basin_name,
    flow_var="inflow",
    flood_var="flood_event",
    time_var="time",
    split_threshold=0.01,
    peak_bias_threshold=0.2,
    volume_bias_threshold=0.2,
    peak_time_bias_threshold=2,
):
    """
    计算洪水预报合格率，并返回详细的指标表格。

    合格标准:
    - 洪峰误差绝对值 <= peak_bias_threshold (默认0.2)
    - 洪量误差绝对值 <= volume_bias_threshold (默认0.2)
    - 峰现时间偏差 <= peak_time_bias_threshold (默认2天)

    参数:
        pred_nc_file (str): 预报nc文件路径.
        obs_nc_file (str): 实测nc文件路径.
        basin_name (str): 流域名称.
        flow_var (str): 流量变量名.
        flood_var (str): 划分洪水场次的事件变量名.
        time_var (str): 时间变量名.
        split_threshold (float): 划分洪水场次的阈值.
        peak_bias_threshold (float): 洪峰误差合格阈值.
        volume_bias_threshold (float): 洪量误差合格阈值.
        peak_time_bias_threshold (float): 峰现时间偏差合格阈值 (单位:天).

    返回:
        tuple: (qualification_rate, results_df, avg_relative_error_level)
            - qualification_rate (float): 合格率 (%).
            - results_df (pd.DataFrame): 包含每场洪水各项指标的详细表格.
            - avg_relative_error_level (float): 平均相对误差水平.
    """
    # 1. 划分洪水场次
    flood_periods = flood_event_split(
        pred_nc_file,
        basin_name=basin_name,
        threshold=split_threshold,
        flood_var=flood_var,
        time_var=time_var,
    )

    if not flood_periods:
        print("未划分出任何洪水场次。")
        return 0.0, pd.DataFrame(), 0.0

    results = []

    # 2. 循环计算各项指标
    for start_time, end_time in flood_periods:
        peak_bias = flood_peak_bias(
            pred_nc_file,
            obs_nc_file,
            basin_name=basin_name,
            flow_var=flow_var,
            start_time=start_time,
            end_time=end_time,
        )
        volume_bias = flood_volume_bias(
            pred_nc_file,
            obs_nc_file,
            basin_name=basin_name,
            flow_var=flow_var,
            start_time=start_time,
            end_time=end_time,
        )
        peak_time_bias = flood_peak_time_bias(
            pred_nc_file,
            obs_nc_file,
            basin_name=basin_name,
            flow_var=flow_var,
            start_time=start_time,
            end_time=end_time,
        )

        # 3. 判断是否合格
        is_qualified = False
        if (
            not np.isnan(peak_bias)
            and not np.isnan(volume_bias)
            and not np.isnan(peak_time_bias)
        ):
            is_qualified = (
                abs(peak_bias) <= peak_bias_threshold
                and abs(volume_bias) <= volume_bias_threshold
                and abs(peak_time_bias) <= peak_time_bias_threshold
            )

        results.append(
            {
                "start_time": start_time,
                "end_time": end_time,
                "peak_bias": peak_bias,
                "volume_bias": volume_bias,
                "peak_time_bias (days)": peak_time_bias,
                "is_qualified": is_qualified,
            }
        )

    # 4. 创建DataFrame并计算合格率
    results_df = pd.DataFrame(results)
    total_events = len(flood_periods)
    qualified_count = results_df["is_qualified"].sum()
    qualification_rate = (
        (qualified_count / total_events) * 100 if total_events > 0 else 0.0
    )

    # 5. 计算平均相对误差水平
    avg_relative_error_level = 1 - results_df["peak_bias"].abs().mean()

    return qualification_rate, results_df, avg_relative_error_level


def test_flood_event():
    """
    测试洪水预报合格率
    """
    pred_nc_file = "/home/zlh/hydroevaluate/data/epoch100flow_pred.nc"
    obs_nc_file = "/home/zlh/hydroevaluate/data/epoch100flow_obs.nc"
    basin_name = "songliao_20800900"

    rate, df, avg_relative_error_level = calculate_flood_forecast_qualification_rate(
        pred_nc_file,
        obs_nc_file,
        basin_name=basin_name,
    )
    print(f"预报合格率: {rate:.2f}%")
    print("详细指标表格:")
    print(df)
    print(f"平均相对误差水平: {avg_relative_error_level:.2f}")

    plot_predobs_with_tp_hydro(
    target_basin_id=basin_name,
    output_folder="/home/zlh/hydroevaluate/data/",
    pred_nc= pred_nc_file,
    obs_nc= obs_nc_file,
    data_path="/home/zlh/HydroDataCompiler/data/songliaorrevent/songliaorrevent",
    precip_var= "rain",
    pred_colunm= "inflow",
    time_unit= "1D",
    time_range=(df["start_time"].iloc[0], df["end_time"].iloc[0]),
)

test_flood_event()
