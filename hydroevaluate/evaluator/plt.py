import os
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties
from hydroutils.hydro_plot import plot_rainfall_runoff
#from torchhydro import CACHE_DIR


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
        plot_rainfall_runoff(
            time,
            precip,
            [obs, pred],
            fig_size=(10, 6),
            title=title_name,
            ylabel=ylabel,
            prcp_ylabel=tp_ylabel,
            leg_lst=["Observation", "Prediction"],
        )

        plt.savefig(f"{output_folder}/{target_basin_id}_{pred_colunm}.png")

        obs_nc.close()
    else:
        print(f"{target_basin_id} not found in {obs_nc}")


def plot_flood_event(
    pred_nc_file,
    obs_nc_file,
    output_path,
    start_time,
    end_time,
    basin_index=0,
    flow_var="inflow",
    precip_var=None,
    title=None,
):
    """
    绘制单场洪水事件的预报与观测流量过程线，并可选择性地附带降雨过程图。

    本函数专门用于可视化指定的单场洪水，对比模型预报和实测流量。

    参数:
    ----------
    pred_nc_file : str
        包含预报数据的nc文件路径。
    obs_nc_file : str
        包含观测数据的nc文件路径。
    output_path : str
        生成的图像文件的完整保存路径 (包括文件名, e.g., 'output/event_1.png')。
    start_time : str or datetime
        洪水事件的开始时间。
    end_time : str or datetime
        洪水事件的结束时间。
    basin_index : int, optional
        目标流域的索引，默认为 0。
    flow_var : str, optional
        nc文件中代表流量的变量名称，默认为 'inflow'。
    precip_var : str, optional
        nc文件中代表降雨的变量名称。如果提供，将在图上方绘制降雨过程。默认为 None。
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

    # 筛选时间和流域
    pred_event_ds = pred_ds.sel(time=slice(start_time, end_time)).isel(
        basin=basin_index
    )
    obs_event_ds = obs_ds.sel(time=slice(start_time, end_time)).isel(basin=basin_index)

    time_coords = obs_event_ds["time"].values
    pred_flow = pred_event_ds[flow_var].values
    obs_flow = obs_event_ds[flow_var].values

    if title is None:
        title = f"Flood Event: {pd.to_datetime(start_time).strftime('%Y-%m-%d')} to {pd.to_datetime(end_time).strftime('%Y-%m-%d')}"

    # 检查输出目录是否存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 绘图
    if precip_var and precip_var in obs_event_ds:
        precip = obs_event_ds[precip_var].values
        plot_rainfall_runoff(
            time_coords,
            precip,
            [obs_flow, pred_flow],
            fig_size=(10, 6),
            title=title,
            ylabel=f"{flow_var} (m^3/s)",
            prcp_ylabel=f"{precip_var} (mm)",
            leg_lst=["Obs", "Pred"],
        )
    else:
        plt.figure(figsize=(12, 6))
        plt.plot(time_coords, obs_flow, label="Obs")
        plt.plot(time_coords, pred_flow, label="Pred", linestyle="--")
        plt.xlabel("Time")
        plt.ylabel(f"{flow_var} (m^3/s)")
        plt.title(title)
        plt.legend()
        plt.grid(True)

    plt.savefig(output_path)
    plt.close()
