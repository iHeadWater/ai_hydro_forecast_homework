"""
Author: zhuanglaihong
Date: 2025-06-24 16:42:48
LastEditTime: 2025-07-07 11:16:22
LastEditors: zhuanglaihong
Description: Flood event rainfall-runoff plotting tools for hydrological evaluation and analysis visualization
FilePath: \hydroevaluate\hydroevaluate\evaluator\rf_plot.py
Copyright: Copyright (c) 2021-2024 zhuanglaihong. All rights reserved.
"""

import os
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties

from hydroutils.hydro_plot import plot_rainfall_runoff
from hydrodatasource.reader.data_source import SelfMadeHydroDataset

# from torchhydro import CACHE_DIR


def load_user_font():
    # 检查字体文件是否存在,如果不存在,则提供下载提示并引发错误
    user_home = os.path.expanduser("~")
    font_path = os.path.join(user_home, ".fonts/SimHei.ttf")
    if not os.path.exists(font_path):
        error_message = (
            f"字体文件 'SimHei.ttf' 未在路径 '{font_path}' 中找到。\n"
            f"为了正确显示图表中的中文,请先安装此字体。\n"
            f"下载地址: https://github.com/StellarCN/scp_zh/tree/master/fonts\n"
            f"请下载 SimHei.ttf 并将其放置在 ~/.fonts/ 目录中,或者修改本文件中的 font_path。"
        )
        raise FileNotFoundError(error_message)
    font_prop = FontProperties(fname=font_path)
    rcParams["font.family"] = font_prop.get_name()
    rcParams["axes.unicode_minus"] = False
    return font_prop


def plot_predobs_with_tp(
    target_basin_id,
    output_folder,
    basin_info_file,
    pred_nc,
    obs_nc,
    basin_column,
    precip_var,
    pred_colunm,
    time_unit,
    time_range=None,
    station_dict=None,
    trans_unit=True,
):
    """
    绘制指定流域的预报与观测流量过程线,并附带降雨过程图。

    本函数用于可视化水文预报结果。它会生成一个标准的"上降雨、下径流"对比图,
    清晰地展示在同一时间段内,模型预报的流量(如 streamflow)与实测流量的吻合程度,
    并关联对应的降雨事件。函数支持从mm/day到m^3/s的单位转换,并会将最终图像保存为文件。

    参数:
    ----------
    target_basin_id : str
        目标流域的ID,用于从nc文件中筛选数据。
    output_folder : str
        生成的图像文件的输出目录。
    basin_info_file : str
        包含流域信息的CSV文件路径,应至少包含流域ID、名称('name')和面积('basin_area')列。
    pred_nc : xr.Dataset or str
        包含预报数据的xarray数据集或nc文件路径。
    obs_nc : xr.Dataset or str
        包含观测数据的xarray数据集或nc文件路径。
    basin_column : str
        nc文件中代表流域维度的坐标名称。
    precip_var : str
        nc文件中代表降雨的变量名称。
    pred_colunm : str
        nc文件中代表预报/观测流量的变量名称(例如 'streamflow')。
    time_unit : str
        数据的时间单位(例如 '1D', '3h', '1h'),用于单位转换和坐标轴标签。
    time_range : tuple, optional
        一个包含(起始时间, 结束时间)的元组,用于限定绘图的时间范围。
        默认为None,即使用数据重叠部分的全时间范围。
    station_dict : dict, optional
        (此参数在当前实现中会被覆盖)包含站点信息的字典。默认为None。
    trans_unit : bool, optional
        是否将流量单位从深度(mm)转换为体积(m^3/s)。默认为True。

    返回:
    -------
    None
        此函数没有返回值,但会将生成的图像以png格式保存到指定的 `output_folder` 中。
    """
    # 1. 读取流域信息
    basin_info = pd.read_csv(basin_info_file)
    basin_area = basin_info.loc[
        basin_info["basin_id"] == target_basin_id, "basin_area"
    ].values[0]
    # 2. 读取流量和降雨
    obs = read_flow_data(obs_nc, target_basin_id, pred_colunm, time_range)
    pred = read_flow_data(pred_nc, target_basin_id, pred_colunm, time_range)
    precip = read_precip_data(obs_nc, target_basin_id, precip_var, time_range)
    # 3. 单位换算
    obs, var_unit = convert_flow_unit(obs, basin_area, time_unit, trans_unit)
    pred, _ = convert_flow_unit(pred, basin_area, time_unit, trans_unit)
    # 4. 绘图
    title_name = f"{target_basin_id}_tp_{pred_colunm}"
    ylabel = f"{pred_colunm} {var_unit}"
    tp_ylabel = f"Precipitation mm/{time_unit}"
    fig, ax = plot_rainfall_runoff(
        obs["time"].values,
        precip,
        [obs, pred],
        fig_size=(10, 6),
        title=title_name,
        ylabel=ylabel,
        prcp_ylabel=tp_ylabel,
        leg_lst=["Observation", "Prediction"],
    )
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper right", fontsize=14)
    fig.tight_layout()
    fig.savefig(f"{output_folder}/{target_basin_id}_{pred_colunm}.png")
    plt.close(fig)

    ax.set_ylabel(ylabel, fontsize=14)
    # 如果plot_rainfall_runoff返回了ax2
    ax2 = ax.twinx()
    ax2.set_ylabel(tp_ylabel, fontsize=14)

    obs_nc.close()


def read_basin_info_from_hydro_dataset(data_path, time_unit):
    """
    从Hydro格式数据集自动读取流域信息,返回DataFrame(含basin_id、area等)。
    :param data_path: Hydro数据集根目录
    :param time_unit: 时间单位(如'1D', '3h', '1h'),可为str或list
    :return: DataFrame,含流域属性
    """
    dataset = SelfMadeHydroDataset(
        data_path=data_path,
        time_unit=[time_unit] if isinstance(time_unit, str) else time_unit,
        offset_to_utc=True,  # 是否有时间偏移
    )
    attrs = dataset.read_site_info()  # DataFrame,含basin_id、area两列
    # dataset 还包含其他数据,这部分直接如何使用
    return attrs


def read_flow_data(
    file_path_or_ds, basin_id, flow_var, time_range=None, file_type=None
):
    """
    读取单个文件的流量数据,支持csv或nc(xarray.Dataset/文件路径)。
    返回结果为DataFrame格式,仅包含指定流域的时间和流量信息,两列分别为'time'和'flow'。

    :param file_path_or_ds: 文件路径或xarray.Dataset
    :param basin_id: 流域ID
    :param flow_var: 流量变量名
    :param time_range: (起始时间, 结束时间),可选
    :param file_type: 'csv'或'nc',自动判断优先
    :return: pd.DataFrame,包含'time'和'flow'两列
    """
    if file_type is None:
        if isinstance(file_path_or_ds, str) and file_path_or_ds.endswith(".csv"):
            file_type = "csv"
        elif isinstance(file_path_or_ds, (xr.Dataset, str)):
            file_type = "nc"
        else:
            raise ValueError("无法判断文件类型")
    if file_type == "csv":
        df = pd.read_csv(file_path_or_ds, parse_dates=["time"])
        if "basin_id" in df.columns:
            df = df[df["basin_id"] == basin_id]
        if time_range is not None:
            start, end = pd.to_datetime(time_range[0]), pd.to_datetime(time_range[1])
            df = df[(df["time"] >= start) & (df["time"] <= end)]
        # 整理为标准格式
        result = df[["time", flow_var]].copy()
        result = result.rename(columns={flow_var: "flow"})
        result = result.reset_index(drop=True)
        return result
    elif file_type == "nc":
        ds = (
            xr.open_dataset(file_path_or_ds)
            if isinstance(file_path_or_ds, str)
            else file_path_or_ds
        )
        da = ds.sel(basin=basin_id)[flow_var]
        if time_range is not None:
            da = da.sel(time=slice(*time_range))
        df = da.to_dataframe().reset_index()
        # 只保留time和flow两列
        result = df[["time", flow_var]].copy()
        result = result.rename(columns={flow_var: "flow"})
        result = result.reset_index(drop=True)
        return result
    else:
        raise ValueError("不支持的文件类型")


def read_precip_data(
    file_path_or_ds, basin_id, precip_var, time_range=None, file_type=None
):
    """
    读取单个文件的降雨数据,支持csv或nc(xarray.Dataset/文件路径)。
    返回结果为DataFrame格式,仅包含指定流域的时间和降雨信息,两列分别为'time'和'precip'。

    :param file_path_or_ds: 文件路径或xarray.Dataset
    :param basin_id: 流域ID
    :param precip_var: 降雨变量名
    :param time_range: (起始时间, 结束时间),可选
    :param file_type: 'csv'或'nc',自动判断优先
    :return: pd.DataFrame,包含'time'和'precip'两列
    """
    if file_type is None:
        if isinstance(file_path_or_ds, str) and file_path_or_ds.endswith(".csv"):
            file_type = "csv"
        elif isinstance(file_path_or_ds, (xr.Dataset, str)):
            file_type = "nc"
        else:
            raise ValueError("无法判断文件类型")
    if file_type == "csv":
        df = pd.read_csv(file_path_or_ds, parse_dates=["time"])
        if "basin_id" in df.columns:
            df = df[df["basin_id"] == basin_id]
        if time_range is not None:
            start, end = pd.to_datetime(time_range[0]), pd.to_datetime(time_range[1])
            df = df[(df["time"] >= start) & (df["time"] <= end)]
        # 整理为标准格式
        result = df[["time", precip_var]].copy()
        result = result.rename(columns={precip_var: "precip"})
        result = result.reset_index(drop=True)
        return result
    elif file_type == "nc":
        ds = (
            xr.open_dataset(file_path_or_ds)
            if isinstance(file_path_or_ds, str)
            else file_path_or_ds
        )
        da = ds.sel(basin=basin_id)[precip_var]
        if time_range is not None:
            da = da.sel(time=slice(*time_range))
        df = da.to_dataframe().reset_index()
        # 只保留time和precip两列
        result = df[["time", precip_var]].copy()
        result = result.rename(columns={precip_var: "precip"})
        result = result.reset_index(drop=True)
        return result
    else:
        raise ValueError("不支持的文件类型")


def convert_flow_unit(flow, basin_area, time_unit, trans_unit=True):
    """
    流量单位换算:mm/时间单位 -> m^3/s
    :param flow: 原始流量(Series/DataArray)
    :param basin_area: 流域面积(单位:km^2)
    :param time_unit: '1D'/'3h'/'1h'
    :param trans_unit: 是否换算为m^3/s
    :return: (换算后流量, 单位字符串)
    """
    if not trans_unit or basin_area is None:
        return flow, f"mm/{time_unit}"
    if time_unit == "1D":
        flow = flow / 24 * basin_area / 3.6
        var_unit = "m^3/s"
    elif time_unit == "3h":
        flow = flow / 3 * basin_area / 3.6
        var_unit = "m^3/s"
    else:  # "1h"
        flow = flow * basin_area / 3.6
        var_unit = "m^3/s"
    return flow, var_unit


def add_metrics_to_figure(fig, legend, metrics_dict):
    """
    在图例下方显示六个指标
    metrics_dict: {
        'individual': {'Peak bias': xx, 'Volume bias': xx, 'Peak time error': xx},
        'regional': {'Peak bias': xx, ...}
    }
    """
    info_str = ""
    for key in metrics_dict:
        info_str += f"{key}:\n"
        for metric, value in metrics_dict[key].items():
            if value is not None:
                info_str += f"{metric}: {value:.3f}\n"
    legend_box = legend.get_window_extent(fig.canvas.get_renderer())
    inv = fig.transFigure.inverted()
    legend_box_fig = inv.transform(legend_box)
    x0, y0 = legend_box_fig[0]
    x1, y1 = legend_box_fig[1]
    info_x = x0 - (x1 - x0) * 0.1
    info_y = y0 - (y1 - y0) * 0.4
    fig.text(
        info_x,
        info_y,
        info_str,
        fontsize=18,
        family="monospace",
        va="top",
        ha="left",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="gray"),
    )


def plot_with_individual_regional(
    target_basin_id,
    output_folder,
    pred_nc,
    obs_nc,
    data_path,
    pred_colunm,
    precip_var,
    time_unit,
    time_range=None,
    trans_unit=True,
    regional_nc=None,
    metrics_dict=None,
):
    """
    功能：
        基于Hydro格式数据集,自动读取指定流域的面积、降雨、观测流量、individual方案预测流量、regional方案预测流量,
        并将三条流量曲线(观测、individual、regional)与降雨过程线绘制在同一张图中。
        同时在图例下方显示individual和regional方案的洪水六个评价指标(峰值偏差、体积偏差、峰现时误差)(可选)。

    参数：
        target_basin_id : str
            目标流域ID
        output_folder : str
            输出图片文件夹
        pred_nc : str 或 xr.Dataset
            individual方案的预测流量nc文件或xarray对象
        obs_nc : str 或 xr.Dataset
            观测流量nc文件或xarray对象
        data_path : str
            Hydro数据集根目录
        pred_colunm : str
            流量变量名(如'streamflow')
        precip_var : str
            降雨变量名(如'precip')
        time_unit : str
            时间单位(如'1D', '3h', '1h')
        time_range : tuple, optional
            (起始时间, 结束时间),如('2020-01-01', '2020-01-10')
        trans_unit : bool, optional
            是否将流量单位换算为m³/s,默认为True
        regional_nc : str 或 xr.Dataset, optional
            regional方案的预测流量nc文件或xarray对象
        metrics_dict : dict, optional
            指标字典,格式为：
            {
                'individual': {'Peak bias': xx, 'Volume bias': xx, 'Peak time error': xx},
                'regional': {'Peak bias': xx, 'Volume bias': xx, 'Peak time error': xx}
            }
            可选参数,如不传入则不显示指标。

    """
    load_user_font()
    # 1. 读取流域面积
    attrs = read_basin_info_from_hydro_dataset(data_path, time_unit)
    try:
        basin_area = attrs.set_index("basin_id").loc[target_basin_id, "area"]
    except Exception as e:
        print(f"无法自动获取流域面积: {e}")
        basin_area = None
    # 2. 读取降雨数据
    precip = None
    try:
        if isinstance(data_path, str):
            data_path = os.path.join(data_path, "timeseries", time_unit)
        else:
            data_path = data_path.timeseries[time_unit]
        if isinstance(data_path, str):
            data_path = os.path.join(data_path, f"{target_basin_id}.csv")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"未找到降雨数据文件: {data_path}")
        
        if data_path.endswith(".csv"):
            precip = read_precip_data(
            data_path, target_basin_id, precip_var, time_range, file_type="csv"
        )
        elif data_path.endswith(".nc"):
            precip = read_precip_data(
            data_path, target_basin_id, precip_var, time_range, file_type="nc"
        )
        else:
            raise ValueError("不支持的降雨数据文件类型")
    except Exception as e:
        print(f"降雨数据读取失败: {e}")
    # 3. 读取流量数据
    obs_df = read_flow_data(
        obs_nc, target_basin_id, pred_colunm, time_range, file_type="nc"
    )
    pred_df = read_flow_data(
        pred_nc, target_basin_id, pred_colunm, time_range, file_type="nc"
    )
    regional_pred_df = None
    if regional_nc is not None:
        regional_pred_df = read_flow_data(
            regional_nc, target_basin_id, pred_colunm, time_range, file_type="nc"
        )

    obs = obs_df['flow']
    pred = pred_df['flow']
    if regional_pred_df is not None:
        regional_pred = regional_pred_df['flow']
    else:
        regional_pred = None

    # 4. 单位换算
    obs, var_unit = convert_flow_unit(obs, basin_area, time_unit, trans_unit)
    pred, _ = convert_flow_unit(pred, basin_area, time_unit, trans_unit)
    if regional_pred is not None:
        regional_pred, _ = convert_flow_unit(
            regional_pred, basin_area, time_unit, trans_unit
        )
    # 5. 组装数据
    time = obs.index if hasattr(obs, "index") else obs["time"]
    flow_list = [obs, pred]
    leg_list = ["obs", "individual pred"]
    color_list = ["green", "blue"]
    linestyle_list = ["-", "--"]
    if regional_pred is not None:
        flow_list.append(regional_pred)
        leg_list.append("regional pred")
        color_list.append("red")
        linestyle_list.append("--")
    # 6. 绘图
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    title_name = f"{target_basin_id}_flood_{pd.to_datetime(time_range[0]).strftime('%Y-%m-%d')}_{pd.to_datetime(time_range[1]).strftime('%Y-%m-%d')}"
    ylabel = f"{pred_colunm} {var_unit}"
    tp_ylabel = f"Precipitation mm/{time_unit}"
    fig, ax = plot_rainfall_runoff(
        time,
        precip['precip'],  
        flow_list,
        fig_size=(16, 9),
        title=title_name,
        ylabel=ylabel,
        prcp_ylabel=tp_ylabel,
        leg_lst=leg_list,
        linewidth=1,
        prcp_interval=20,
        color_list=color_list,
        linestyle_list=linestyle_list,
    )
    ax.tick_params(axis="x", rotation=45)
    legend = ax.legend(loc="upper right", fontsize=20)
    fig.tight_layout()
    # 7. 指标显示(可选)
    if metrics_dict is not None:
        add_metrics_to_figure(fig, legend, metrics_dict)
    # 8. 保存
    fig.savefig(f"{output_folder}/{title_name}.png")
    plt.close(fig)


def plot_long_series_with_hydro(
    target_basin_id,
    data_path,
    output_folder,
    pred_nc,
    obs_nc,
    flow_var,
    precip_var,
    time_unit,
    time_range=None,
    trans_unit=True
):
    """
    绘制长序列降雨径流图。
    读取Hydro数据集下指定流域的csv时序降雨数据,
    并从两个nc文件读取观测和预测流量,
    截取指定时间段，绘制长时序“上降雨、下流量”图（观测+预测）。

    参数:
    ----------
    target_basin_id : str
        流域ID
    data_path : str
        Hydro数据集根目录
    output_folder : str
        输出图片文件夹
    pred_nc : str or xr.Dataset
        预测流量nc文件路径或xarray对象
    obs_nc : str or xr.Dataset
        观测流量nc文件路径或xarray对象
    flow_var : str
        nc文件中流量变量名
    precip_var : str
        csv文件中降雨量列名
    time_unit : str
        时间单位（如'1D', '1h'）
    time_range : tuple, optional
        (起始时间, 结束时间)
    trans_unit : bool, optional
        是否单位换算为m^3/s
    """
    load_user_font()
    # 1. 读取流域属性
    dataset = SelfMadeHydroDataset(data_path=data_path, time_unit=[time_unit])
    attrs = dataset.read_site_info()
    basin_area = attrs.set_index("basin_id").loc[target_basin_id, "area"]
    # 2. 读取降雨数据（csv）
    csv_path = os.path.join(data_path, "timeseries", time_unit, f"{target_basin_id}.csv")
    if not os.path.exists(csv_path):
        print(f"未找到降雨数据文件: {csv_path}")
        return
    df = pd.read_csv(csv_path, parse_dates=["time"])
    # 3. 读取观测和预测流量（nc文件）
    obs_ds = xr.open_dataset(obs_nc) if isinstance(obs_nc, str) else obs_nc
    pred_ds = xr.open_dataset(pred_nc) if isinstance(pred_nc, str) else pred_nc
    obs = obs_ds.sel(basin=target_basin_id)[flow_var]
    pred = pred_ds.sel(basin=target_basin_id)[flow_var]
    # 4. 截取时间区间
    if time_range is not None:
        time_start, time_end = pd.to_datetime(time_range[0]), pd.to_datetime(time_range[1])
        df = df[(df["time"] >= time_start) & (df["time"] <= time_end)]
        obs = obs.sel(time=slice(time_start, time_end))
        pred = pred.sel(time=slice(time_start, time_end))
    time = df["time"]
    precip = df[precip_var]
    # 5. 单位换算
    if trans_unit and basin_area is not None:
        if time_unit == "1D":
            obs = obs / 24 * basin_area / 3.6
            pred = pred / 24 * basin_area / 3.6
            var_unit = "m^3/s"
        elif time_unit == "3h":
            obs = obs / 3 * basin_area / 3.6
            pred = pred / 3 * basin_area / 3.6
            var_unit = "m^3/s"
        else:  # "1h"
            obs = obs * basin_area / 3.6
            pred = pred * basin_area / 3.6
            var_unit = "m^3/s"
    else:
        var_unit = f"m^3/s"
    # 6. 绘图
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    title_name = f"{target_basin_id}_long_series_{time.iloc[0].strftime('%Y-%m-%d')}_{time.iloc[-1].strftime('%Y-%m-%d')}"
    ylabel = f"{flow_var} {var_unit}"
    tp_ylabel = f"Precipitation mm/{time_unit}"
    # 获取所有序列的长度
    n_time = len(time)
    n_obs = len(obs)
    n_pred = len(pred)
    n_precip = len(precip)

    # 取最短长度
    min_len = min(n_time, n_obs, n_pred, n_precip)

    # 截断所有序列到相同长度
    time = time[:min_len]
    obs = obs[:min_len]
    pred = pred[:min_len]
    precip = precip[:min_len]

    fig, ax = plot_rainfall_runoff(
        time,
        precip,
        [obs, pred],
        fig_size=(16, 9),
        title=title_name,
        ylabel=ylabel,
        prcp_ylabel=tp_ylabel,
        leg_lst=["Observation", "Prediction"],
        linewidth=1,
        prcp_interval=20,
        color_list=["green", "red"],  # 观测为绿色，预测为红色
        linestyle_list=["-", "--"]
    )
    ax.tick_params(axis='x', rotation=45)
    ax.legend(loc='upper right', fontsize=14)
    fig.tight_layout()
    fig.savefig(f"{output_folder}/{title_name}.png")
    plt.close(fig)
    print(f"图片已保存至: {output_folder}/{title_name}.png")


if __name__ == "__main__":
    # 示例:读取流域信息
    # data_path = '/data/songliaorrevent'
    # time_unit = '1D'
    # attrs = read_basin_info_from_hydro_dataset(data_path, time_unit)
    # print(attrs)

    # 示例:读取流量数据
    # file_path = '/data/epochbest_model.pthflow_obs.nc'
    # basin_id = 'songliao_21401550'
    # flow_var = 'streamflow'
    # time_range = ('2020-01-01', '2020-01-31')
    # flow_data = read_flow_data(file_path, basin_id, flow_var, time_range, file_type='nc')
    # print(flow_data)

    # 示例:绘制降雨径流图
    metrics_dict = {
        "individual": {"Peak bias": 0.1, "Volume bias": 0.2, "Peak time error": 1.0},
        "regional": {"Peak bias": 0.05, "Volume bias": 0.1, "Peak time error": 0.5},
    }
    plot_with_individual_regional(
        target_basin_id="001",
        output_folder="./output",
        pred_nc="indiv_pred.nc",
        obs_nc="obs.nc",
        data_path="./hydrodata",
        pred_colunm="streamflow",
        precip_var="precip",
        time_unit="1D",
        time_range=("2020-01-01", "2020-01-10"),
        metrics_dict=metrics_dict,
    )
