import os
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.font_manager import FontProperties
from torchhydro import CACHE_DIR


def load_user_font():
    user_home = os.path.expanduser("~")
    font_path = os.path.join(user_home, ".fonts/SimHei.ttf")
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
            obs,
            precip,
            pred,
            title_name,
            ylabel,
            tp_ylabel,
        )

        plt.savefig(f"{output_folder}/{target_basin_id}_{pred_colunm}.png")

        obs_nc.close()
    else:
        print(f"{target_basin_id} not found in {obs_nc}")


def plot_rainfall_runoff(
    time,
    obs,
    precip,
    pred,
    title_name,
    output_ylabel,
    tp_ylabel,
    font_prop=None,
):
    if font_prop is None:
        font_prop = load_user_font()

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.bar(time, precip, width=0.1, color="blue", alpha=0.6, label="Precipitation")
    ax1.set_ylabel(tp_ylabel, color="blue", fontproperties=font_prop)
    ax1.tick_params(axis="y", labelcolor="blue")

    ax1.set_ylim(0, precip.max() * 5)
    ax1.invert_yaxis()

    ax2 = ax1.twinx()

    # transform the unit of obs and pred
    ax2.plot(
        time,
        obs,
        color="green",
        linestyle="-",
        label="observed value",
    )
    ax2.plot(
        time,
        pred,
        color="red",
        linestyle="--",
        label="predicted value",
    )

    ax2.set_ylabel(output_ylabel, color="red", fontproperties=font_prop)
    ax2.tick_params(axis="y", labelcolor="red")

    plt.title(
        title_name,
        fontproperties=font_prop,
    )

    plt.legend(loc="upper left")


def get_nc_files(target_basin_id, time_unit):

    for file_name in os.listdir(CACHE_DIR):
        if file_name.endswith(".nc") and time_unit in file_name:
            file_path = os.path.join(CACHE_DIR, file_name)

            try:
                # open the dataset
                dataset = xr.open_dataset(file_path)

                # check if the dataset contains the basin column
                if "basin" in dataset:
                    # get all basin ids
                    basin_ids = dataset["basin"].values

                    if target_basin_id in basin_ids:
                        print(f"Found basin {target_basin_id} in file: {file_name}")
                        dataset.close()
                        return file_path
                    else:
                        dataset.close()
                        # print(f"basin {target_basin_id} not found in file: {file_name}")
                else:
                    dataset.close()
                    # print(f"basin not found in file: {file_name}")

            except Exception as e:
                print(f"Error reading {file_name}: {e}")
    return None
