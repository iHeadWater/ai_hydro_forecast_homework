"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 10:41:42
LastEditors: zhuanglaihong
LastEditTime: 2025-06-24 16:05:58
FilePath: \hydroevaluate\hydroevaluate\evaluator\eval.py
Description: 
"""

import warnings
import numpy as np
import pandas as pd
import xarray as xr

from hydroevaluate.evaluator.rf_plot import  plot_predobs_with_tp_hydro,plot_flood_event_with_hydro


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
    # 只取该流域的流量和时间
    pred_da = ds_pred[flow_var].sel(basin=basin_name)
    obs_da = ds_obs[flow_var].sel(basin=basin_name)
    times = pred_da[time_var].values
    flow_pred = pred_da.values
    flow_obs = obs_da.values

    if start_time is None or end_time is None:
        raise ValueError("请输入start_time和end_time用于单场洪水分析。")

    # 保证时间类型一致
    start_time = np.datetime64(start_time)
    end_time = np.datetime64(end_time)

    mask = (times >= start_time) & (times <= end_time)
    # 新增：如果mask和flow_obs长度不一致，直接返回0
    if len(mask) != len(flow_obs):
        return 0.0

    if not np.any(mask):
        return 0.0

    pred_peak = np.max(flow_pred[mask])
    obs_peak = np.max(flow_obs[mask])
    return 0.0 if obs_peak == 0 else (pred_peak - obs_peak) / obs_peak


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
    # 只取该流域的流量和时间
    pred_da = pred_ds[flow_var].sel(basin=basin_name)
    obs_da = obs_ds[flow_var].sel(basin=basin_name)
    times = pred_da[time_var].values
    pred_flow = pred_da.values
    obs_flow = obs_da.values

    start_time = np.datetime64(start_time)
    end_time = np.datetime64(end_time)
    mask = (times >= start_time) & (times <= end_time)
    # 新增：如果mask和obs_flow长度不一致，直接返回0
    if len(mask) != len(obs_flow):
        return 0.0
    if not np.any(mask):
        return 0.0
    # 只取区间内数据
    times_sel = times[mask]
    pred_flow_sel = pred_flow[mask]
    obs_flow_sel = obs_flow[mask]
    if len(times_sel) == 0 or len(pred_flow_sel) == 0 or len(obs_flow_sel) == 0:
        return 0.0
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
    # 只取该流域的流量和时间
    pred_da = pred_ds[flow_var].sel(basin=basin_name)
    obs_da = obs_ds[flow_var].sel(basin=basin_name)
    times = pred_da[time_var].values
    pred_flow = pred_da.values
    obs_flow = obs_da.values

    start_time = np.datetime64(start_time)
    end_time = np.datetime64(end_time)
    mask = (times >= start_time) & (times <= end_time)
    # 新增：如果mask和obs_flow长度不一致，直接返回0
    if len(mask) != len(obs_flow):
        return 0.0
    if not np.any(mask):
        return 0.0
    pred_volume = np.sum(pred_flow[mask])
    obs_volume = np.sum(obs_flow[mask])
    if obs_volume == 0:
        return 0.0
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



def evaluate_multi_basin_flood_forecast(
    pred_nc_file,
    obs_nc_file,
    flow_var="inflow",
    time_var="time",
    peak_bias_threshold=0.2,
    volume_bias_threshold=0.2,
    peak_time_bias_threshold=2,
):
    """
    多流域长序列洪水预报评估：每个流域全时段视为一场洪水，计算洪峰误差、洪量误差、峰现时间偏差。

    参数：
        pred_nc_file (str): 预报nc文件路径
        obs_nc_file (str): 实测nc文件路径
        flow_var (str): 流量变量名
        time_var (str): 时间变量名
        peak_bias_threshold (float): 洪峰误差合格阈值
        volume_bias_threshold (float): 洪量误差合格阈值
        peak_time_bias_threshold (float): 峰现时间偏差合格阈值（单位：天）
    返回：
        pd.DataFrame: 每个流域一行，包含各项指标和是否合格
    """
    ds_pred = xr.open_dataset(pred_nc_file)
    ds_obs = xr.open_dataset(obs_nc_file)
    basin_ids = ds_pred["basin"].values
    times = ds_pred[time_var].values
    start_time = times[0]
    end_time = times[-1]
    results = []
    for basin in basin_ids:
        pred_flow = ds_pred[flow_var].sel(basin=basin).values
        obs_flow = ds_obs[flow_var].sel(basin=basin).values

        # 跳过全为NaN的流域
        if np.all(np.isnan(pred_flow)) or np.all(np.isnan(obs_flow)):
            results.append({
                "basin": basin,
                "start_time": start_time,
                "end_time": end_time,
                "peak_bias": np.nan,
                "volume_bias": np.nan,
                "peak_time_bias (days)": np.nan,
                "is_qualified": False,
            })
            continue

        # 后续计算保持不变
        pred_peak = np.nanmax(pred_flow)
        obs_peak = np.nanmax(obs_flow)
        peak_bias = np.nan if obs_peak == 0 else (pred_peak - obs_peak) / obs_peak
        pred_volume = np.nansum(pred_flow)
        obs_volume = np.nansum(obs_flow)
        volume_bias = np.nan if obs_volume == 0 else (pred_volume - obs_volume) / obs_volume
        pred_peak_idx = np.nanargmax(pred_flow)
        obs_peak_idx = np.nanargmax(obs_flow)
        pred_peak_time = times[pred_peak_idx]
        obs_peak_time = times[obs_peak_idx]
        try:
            peak_time_bias = (np.datetime64(pred_peak_time) - np.datetime64(obs_peak_time)) / np.timedelta64(1, "D")
        except Exception:
            peak_time_bias = np.nan
        is_qualified = (
            not np.isnan(peak_bias)
            and not np.isnan(volume_bias)
            and not np.isnan(peak_time_bias)
            and abs(peak_bias) <= peak_bias_threshold
            and abs(volume_bias) <= volume_bias_threshold
            and abs(peak_time_bias) <= peak_time_bias_threshold
        )
        results.append({
            "basin": basin,
            "start_time": start_time,
            "end_time": end_time,
            "peak_bias": peak_bias,
            "volume_bias": volume_bias,
            "peak_time_bias (days)": peak_time_bias,
            "is_qualified": is_qualified,
        })
    df = pd.DataFrame(results)
    return df



def test_flood_event():
    """
    测试洪水预报合格率
    """
    basin_name = "songliao_20800900"
    pred_nc_file = "/home/zlh/hydroevaluate/data/events_train_3h/songliao_20800900_hybrid_loss/epoch15flow_pred.nc"
    obs_nc_file = "/home/zlh/hydroevaluate/data/events_train_3h/songliao_20800900_hybrid_loss/epoch15flow_obs.nc"
    data_path="/home/zlh/HydroDataCompiler/data/songliaorrevent/songliaorrevent"
    

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
        pred_nc=pred_nc_file,
        obs_nc= obs_nc_file,
        pred_colunm="inflow",
        precip_var="rain",
        data_path=data_path,
        output_folder="/home/zlh/hydroevaluate/resultss",
        time_unit='3h',
        time_range=(df['start_time'].iloc[0], df['end_time'].iloc[0]),
        trans_unit=True,     
        peak_bias=df['peak_bias'].iloc[3], 
        volume_bias =df['volume_bias'].iloc[3], 
        peak_time_bias= df['peak_time_bias (days)'].iloc[3],
    )

    '''
    plot_flood_event_with_hydro(
    target_basin_id= basin_name,
    data_path="/home/zlh/HydroDataCompiler/data/songliaorrevent/songliaorrevent",
    output_folder="./output",
    flow_var="inflow",
    time_unit="3h",
    time_range=(df['start_time'].iloc[3], df['end_time'].iloc[3]),
    trans_unit=True,
    precip_var="rain" ,
    )
    '''


def plot_flood_event():
    """
    批量划分和绘图
    """
    
    basin_name_all = ["songliao_20800900",
                      "songliao_20810200",
                    "songliao_21100150",
                    "songliao_21110150",
                    "songliao_21401050",
                    "songliao_21401550",
                      ]
    for basin_name in basin_name_all:
        pred_nc_file = f"/home/zlh/hydroevaluate/data/events_dpl_train_oy_PET/{basin_name}_hybrid_loss/epoch20flow_pred.nc"
        obs_nc_file = f"/home/zlh/hydroevaluate/data/events_dpl_train_oy_PET/{basin_name}_hybrid_loss/epoch20flow_obs.nc"
        data_path = "/home/zlh/HydroDataCompiler/data/songliaorrevent/songliaorrevent"

        rate, df1, avg_relative_error_level = calculate_flood_forecast_qualification_rate(
            pred_nc_file,
            obs_nc_file,
            basin_name=basin_name,
        )
        
        rate, df2, avg_relative_error_level = calculate_flood_forecast_qualification_rate(
            pred_nc_file="/home/zlh/hydroevaluate/data/events_dpl_train_oy_PET/regional_hybrid_loss/epoch20flow_pred.nc",
            obs_nc_file ="/home/zlh/hydroevaluate/data/events_dpl_train_oy_PET/regional_hybrid_loss/epoch20flow_obs.nc",
            basin_name=basin_name,
        )
        for i, row in df1.iterrows():
            # 在df2中找到对应时间段的regional指标
            matching_row = df2[(df2['start_time'] == row['start_time']) & (df2['end_time'] == row['end_time'])]
            if not matching_row.empty:
                regional_peak_bias = matching_row['peak_bias'].iloc[0]
                regional_volume_bias = matching_row['volume_bias'].iloc[0]
                regional_peak_time_bias = matching_row['peak_time_bias (days)'].iloc[0]
            else:
                regional_peak_bias = None
                regional_volume_bias = None
                regional_peak_time_bias = None
                
            plot_predobs_with_tp_hydro(
                target_basin_id=basin_name,
                pred_nc=pred_nc_file,
                obs_nc=obs_nc_file,
                pred_colunm="inflow",
                precip_var="rain",
                data_path=data_path,
                output_folder=f"/home/zlh/hydroevaluate/results_dpl_train_oy_PET/{basin_name}",
                time_unit='3h',
                time_range=(row['start_time'], row['end_time']),
                trans_unit=True,
                peak_bias=row['peak_bias'],
                volume_bias=row['volume_bias'],
                peak_time_bias=row['peak_time_bias (days)'],
                regional_nc="/home/zlh/hydroevaluate/data/events_dpl_train_oy_PET/regional_hybrid_loss/epoch20flow_pred.nc",
                regional_peak_bias=regional_peak_bias,
                regional_volume_bias=regional_volume_bias,
                regional_peak_time_bias=regional_peak_time_bias
            )
            

plot_flood_event()