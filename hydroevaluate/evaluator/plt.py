import os
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties
import sys
sys.path.append("/home/zlh/hydrodatasource")

from hydroutils.hydro_plot import plot_rainfall_runoff
from hydrodatasource.reader.data_source import SelfMadeHydroDataset

# from torchhydro import CACHE_DIR


def load_user_font():
    # 检查字体文件是否存在，如果不存在，则提供下载提示并引发错误
    user_home = os.path.expanduser("~")
    font_path = os.path.join(user_home, ".fonts/SimHei.ttf")
    if not os.path.exists(font_path):
        error_message = (
            f"字体文件 'SimHei.ttf' 未在路径 '{font_path}' 中找到。\n"
            f"为了正确显示图表中的中文，请先安装此字体。\n"
            f"下载地址: https://github.com/StellarCN/scp_zh/tree/master/fonts\n"
            f"请下载 SimHei.ttf 并将其放置在 ~/.fonts/ 目录中，或者修改本文件中的 font_path。"
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
    绘制指定流域的预报与观测流量过程线，并附带降雨过程图。

    本函数用于可视化水文预报结果。它会生成一个标准的"上降雨、下径流"对比图，
    清晰地展示在同一时间段内，模型预报的流量（如 streamflow）与实测流量的吻合程度，
    并关联对应的降雨事件。函数支持从mm/day到m³/s的单位转换，并会将最终图像保存为文件。

    参数:
    ----------
    target_basin_id : str
        目标流域的ID，用于从nc文件中筛选数据。
    output_folder : str
        生成的图像文件的输出目录。
    basin_info_file : str
        包含流域信息的CSV文件路径，应至少包含流域ID、名称('name')和面积('basin_area')列。
    pred_nc : xr.Dataset or str
        包含预报数据的xarray数据集或nc文件路径。
    obs_nc : xr.Dataset or str
        包含观测数据的xarray数据集或nc文件路径。
    basin_column : str
        nc文件中代表流域维度的坐标名称。
    precip_var : str
        nc文件中代表降雨的变量名称。
    pred_colunm : str
        nc文件中代表预报/观测流量的变量名称（例如 'streamflow'）。
    time_unit : str
        数据的时间单位（例如 '1D', '3h', '1h'），用于单位转换和坐标轴标签。
    time_range : tuple, optional
        一个包含(起始时间, 结束时间)的元组，用于限定绘图的时间范围。
        默认为None，即使用数据重叠部分的全时间范围。
    station_dict : dict, optional
        (此参数在当前实现中会被覆盖)包含站点信息的字典。默认为None。
    trans_unit : bool, optional
        是否将流量单位从深度(mm)转换为体积(m³/s)。默认为True。

    返回:
    -------
    None
        此函数没有返回值，但会将生成的图像以png格式保存到指定的 `output_folder` 中。
    """
    basin_info = pd.read_csv(basin_info_file)
    time_start, time_end = time_range
    # TODO: make the function more general
    if pred_colunm == "streamflow":
        var_unit = "m^3/s" if trans_unit else "mm/" + time_unit
    elif pred_colunm == "sm_surface":
        var_unit = "m^3/m^3"
    else:
        var_unit = None
    tp_unit = "mm/" + time_unit
    if time_unit == "3h":
        time_end = pd.to_datetime(time_end) + pd.Timedelta(hours=1)
        time_start = pd.to_datetime(time_start) + pd.Timedelta(hours=1)
    else:
        time_start = pd.to_datetime(time_start)
        time_end = pd.to_datetime(time_end)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if target_basin_id in obs_nc[basin_column].values:
        # print(f"Processing {nc_file} with basin_id {target_basin_id}")

        # extract the data for the target basin
        basin_data = obs_nc.sel({basin_column: target_basin_id})
        obs = obs_nc.sel({basin_column: target_basin_id})[pred_colunm]

        pred = pred_nc.sel({basin_column: target_basin_id})[pred_colunm]

        # if time_start and time_end are provided, adjust the time range
        if time_start and time_end:
            try:
                # obtain the time range of obs and pred
                obs_time_range = obs.time
                pred_time_range = pred.time

                # adjust the time range to the maximum overlap
                flow_time_start = max(
                    time_start,
                    obs_time_range.min().values,
                    pred_time_range.min().values,
                )
                flow_time_end = min(
                    time_end,
                    obs_time_range.max().values,
                    pred_time_range.max().values,
                )

                # select the data within the time range
                basin_data = basin_data.sel(time=slice(flow_time_start, flow_time_end))

            except Exception as e:
                print(f"Error: {e}")
                return None

        # extract the time and precipitation data
        time = basin_data["time"]
        precip = basin_data[precip_var]

        # extract the flow data
        obs = obs.sel(time=slice(flow_time_start, flow_time_end))
        pred = pred.sel(time=slice(flow_time_start, flow_time_end))

        station_dict = basin_info.set_index("basin_id")[["name", "basin_area"]].to_dict(
            orient="index"
        )

        if target_basin_id in station_dict:

            basin_info = station_dict[target_basin_id]

            target_basin_id = basin_info["name"]

            basin_area = basin_info["basin_area"]
        else:

            print(f"{target_basin_id} not found in station_dict")
        if trans_unit:
            if time_unit == "1D":
                obs_hourly = obs / 24
                obs = obs_hourly * basin_area / 3.6
                pred_hourly = pred / 24
                pred = pred_hourly * basin_area / 3.6

            elif time_unit == "3h":
                obs_hourly = obs / 3
                obs = obs_hourly * basin_area / 3.6
                pred_hourly = pred / 3
                pred = pred_hourly * basin_area / 3.6

            else:  # time_unit == '1h'
                obs = obs * basin_area / 3.6
                pred = pred * basin_area / 3.6
        title_name = f"{target_basin_id}_tp_{pred_colunm}"
        ylabel = f"{pred_colunm} {var_unit}"
        tp_ylabel = f"Precipitation {tp_unit}"
        fig, ax = plot_rainfall_runoff(
            time,
            precip,
            [obs, pred],
            fig_size=(10, 6),
            title=title_name,
            ylabel=ylabel,
            prcp_ylabel=tp_ylabel,
            leg_lst=["Observation", "Prediction"],
        )
        ax.tick_params(axis='x', rotation=45)
        ax.legend(loc='upper right', fontsize=14)
        fig.tight_layout()
        fig.savefig(f"{output_folder}/{target_basin_id}_{pred_colunm}.png")
        plt.close(fig)

        ax.set_ylabel(ylabel, fontsize=14)
        # 如果plot_rainfall_runoff返回了ax2
        ax2 = ax.twinx()
        ax2.set_ylabel(tp_ylabel, fontsize=14)

        obs_nc.close()
    else:
        print(f"{target_basin_id} not found in {obs_nc}")


def plot_predobs_with_tp_hydro(
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
):
    """
    基于Hydro格式数据集自动读取流域信息和降雨数据，绘制指定流域的预报与观测流量过程线，并附带降雨过程图。

    参数:
    ----------
    target_basin_id : str
        目标流域的ID。
    output_folder : str
        输出图片文件夹。
    pred_nc : xr.Dataset or str
        预报数据nc文件或xarray对象。
    obs_nc : xr.Dataset or str
        观测数据nc文件或xarray对象。
    data_path : str
        Hydro格式数据集根目录。
    pred_colunm : str
        预报/观测流量变量名。
    precip_var : str
        nc文件中代表降雨的变量名称。
    time_unit : str
        时间单位（如'1D'）。
    time_range : tuple, optional
        (起始时间, 结束时间)。
    trans_unit : bool, optional
        是否单位换算为m³/s。
    """
    load_user_font()
    # 1. 读取Hydro数据集，获取流域属性
    dataset = SelfMadeHydroDataset(
        data_path=data_path,
        time_unit=[time_unit],
        offset_to_utc=True,
    )
    attrs = dataset.read_site_info()  # DataFrame，含basin_id、area等
    station_dict = attrs.set_index("basin_id")[["area"]].to_dict(orient="index")
    # 2. 读取降雨数据
    if time_range is not None:
        time_start, time_end = time_range
    else:
        # 自动获取nc文件时间范围
        obs_ds = xr.open_dataset(obs_nc) if isinstance(obs_nc, str) else obs_nc
        times = obs_ds["time"].values
        time_start = pd.to_datetime(times[0])
        time_end = pd.to_datetime(times[-1])
    precip_data = dataset.read_timeseries(
        object_ids=[target_basin_id],
        t_range_list=[time_start, time_end],
        relevant_cols=[precip_var]
    )
    precip = precip_data[time_unit][0, :, 0]
    # 3. 读取流量数据
    obs_ds = xr.open_dataset(obs_nc) if isinstance(obs_nc, str) else obs_nc
    pred_ds = xr.open_dataset(pred_nc) if isinstance(pred_nc, str) else pred_nc
    obs = obs_ds.sel(basin=target_basin_id)[pred_colunm].sel(time=slice(time_start, time_end))
    pred = pred_ds.sel(basin=target_basin_id)[pred_colunm].sel(time=slice(time_start, time_end))
    time = obs["time"].values
    # 4. 单位换算
    basin_area = station_dict[target_basin_id]["area"] if target_basin_id in station_dict else None
    if trans_unit and basin_area is not None:
        if time_unit == "1D":
            obs_hourly = obs / 24
            obs = obs_hourly * basin_area / 3.6
            pred_hourly = pred / 24
            pred = pred_hourly * basin_area / 3.6
        elif time_unit == "3h":
            obs_hourly = obs / 3
            obs = obs_hourly * basin_area / 3.6
            pred_hourly = pred / 3
            pred = pred_hourly * basin_area / 3.6
        else:  # time_unit == '1h'
            obs = obs * basin_area / 3.6
            pred = pred * basin_area / 3.6
        var_unit = "m^3/s"
    else:
        var_unit = "mm/" + time_unit
    # 5. 绘图
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    title_name = f"{target_basin_id}_tp_{pred_colunm}"
    ylabel = f"{pred_colunm} {var_unit}"
    tp_ylabel = f"Precipitation mm/{time_unit}"
    fig, ax = plot_rainfall_runoff(
        time,
        precip,
        [obs, pred],
        fig_size=(16, 9),
        title=title_name,
        ylabel=ylabel,
        prcp_ylabel=tp_ylabel,
        leg_lst=["obs", "pred"],
        linewidth=1, # 设置线宽
        prcp_interval=20,# 设置降雨间隔
    )

    ax.tick_params(axis='x', rotation=45)
    ax.legend(loc='upper right', fontsize=24) # 图例
    fig.tight_layout()
    fig.savefig(f"{output_folder}/{target_basin_id}_{pred_colunm}.png")
    plt.close(fig)

    
