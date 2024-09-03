"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2024-05-31 13:35:19
LastEditors: Wenyu Ouyang
Description: some common functions
FilePath: \\hydroevaluate\\hydroevaluate\\utils\\heutils.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from matplotlib import pyplot as plt
import urllib3 as ur
from yaml import Loader, load

import datetime
import xarray as xr
import pint

import os.path
import pandas as pd

ureg = pint.UnitRegistry()
ureg.setup_matplotlib()

import xarray as xr

def convert_units(data, units, area=None):
    for var_name, (from_unit, to_unit) in units.items():
        if var_name in data:
            # Retrieve the variable from the dataset
            var_data = data[var_name]
            
            # Unit conversion logic
            if from_unit == "mm/h" and to_unit == "mm/3h":
                data[var_name] = var_data * 3
            elif from_unit == "m/h" and to_unit == "mm/3h":
                data[var_name] = var_data * 1000 * 3
            elif from_unit in ["m^3/s", "ft^3/s"] and to_unit == "mm/h":
                if area is None:
                    raise ValueError("Area is required to convert flow to depth.")
                if from_unit == "ft^3/s":
                    # Use pint to convert from ft^3/s to m^3/s
                    quantity = var_data.values * ureg(from_unit)
                    var_data_m3s = quantity.to("m^3/s").magnitude
                    var_data = xr.DataArray(var_data_m3s, coords=var_data.coords, dims=var_data.dims)
                # Convert flow from m^3/s to mm/h
                data[var_name] = (var_data / area) * 3.6
            else:
                # Handle other unit conversions
                quantity = var_data.values * ureg(from_unit)
                converted_quantity = quantity.to(to_unit).magnitude
                data[var_name] = xr.DataArray(converted_quantity, coords=var_data.coords, dims=var_data.dims)
    return data

def read_yaml(version):
    config_path = os.path.join(
        work_dir, f'test_data/aiff_config/aiff_v{str(version)}.yml'
    )
    if not os.path.exists(config_path):
        version_url = f'https://raw.githubusercontent.com/iHeadWater/AIFloodForecast/main/scripts/conf/v{str(version)}.yml'
        yml_str = ur.request('GET', version_url).data.decode('utf8')
    else:
        with open(config_path, 'r') as fp:
            yml_str = fp.read()
    return load(yml_str, Loader=Loader)


def convert_baseDatetime_iso(record, key):
    # 解析 ISO 8601 日期时间字符串
    dt = datetime.datetime.fromisoformat(record[key].replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def to_dataarray(df, dims, coords, name):
    # 将数据转换为 xarray.DataArray
    return xr.DataArray(df[name].values, dims=dims, coords=coords, name=name)


def gee_gpm_to_1h_data(csv_path):
    """
    Convert GEE GPM half-hour data to 1h data

    Parameters
    ----------
    csv_path : _type_
        _description_

    Returns
    -------
    pd.DataFrame
        _description_
    """
    # Load the CSV file, ensuring BASIN_ID is read as a string
    data = pd.read_csv(csv_path)

    # Convert 'time_start' to datetime
    data["time_start"] = pd.to_datetime(data["time_start"])

    # Set 'time_start' as index for resampling
    data.set_index("time_start", inplace=True)

    # Resample to hourly frequency, taking the mean for 'precipitationCal'
    resampled_data = data.resample("H").mean()

    # Reset index to move 'time_start' back to a column
    resampled_data.reset_index(inplace=True)

    return resampled_data

def calculate_nse(observed_csv_path, simulated_csv_path, column_name):
    """
    calculate_nse

    Parameters
    ----------
    observed_csv : str
        path of observed csv
    simulated_csv : str
        path of simulated csv
    column_name : str
        column name of csv

    Returns
    -------
    nse : float
        NSE value

    Raises
    ------
    ValueError
        If either CSV file does not contain a 'time' column
    """
    # read csv file
    observed_df = pd.read_csv(observed_csv_path)
    simulated_df = pd.read_csv(simulated_csv_path)

    # check if both CSV files contain a 'time' column
    if "time" in observed_df.columns and "time" in simulated_df.columns:
        time_column = "time"
    elif "time_start" in observed_df.columns and "time_start" in simulated_df.columns:
        time_column = "time_start"
    else:
        raise ValueError("Both CSV files must contain a 'time' or 'time_start' column")

    # convert 'time' column to datetime
    observed_df[time_column] = pd.to_datetime(observed_df[time_column])
    simulated_df[time_column] = pd.to_datetime(simulated_df[time_column])

    # merge the two CSV files on the 'time' column
    merged_df = pd.merge(
        observed_df, simulated_df, on=time_column, suffixes=("_obs", "_sim")
    )

    # calculate NSE
    observed = merged_df[f"{column_name}_obs"]
    simulated = merged_df[f"{column_name}_sim"]
    observed_mean = observed.mean()
    numerator = ((observed - simulated) ** 2).sum()
    denominator = ((observed - observed_mean) ** 2).sum()
    return 1 - (numerator / denominator) # NSE


def plot_time_series(observed_csv, simulated_csv, column_name):
    """
    plot_time_series

    Parameters
    ----------
    observed_csv : str
        path of observed csv
    simulated_csv : str
        path of simulated csv
    column_name : str
        column name of csv

    Raises
    ------
    ValueError
        If either CSV file does not contain a 'time' column
    """
    # read csv file
    observed_df = pd.read_csv(observed_csv)
    simulated_df = pd.read_csv(simulated_csv)

    # check if both CSV files contain a 'time' column
    if "time" in observed_df.columns and "time" in simulated_df.columns:
        time_column = "time"
    elif "time_start" in observed_df.columns and "time_start" in simulated_df.columns:
        time_column = "time_start"
    else:
        raise ValueError("Both CSV files must contain a 'time' or 'time_start' column")

    # convert 'time' column to datetime
    observed_df[time_column] = pd.to_datetime(observed_df[time_column])
    simulated_df[time_column] = pd.to_datetime(simulated_df[time_column])

    # merge the two CSV files on the 'time' column
    merged_df = pd.merge(
        observed_df, simulated_df, on=time_column, suffixes=("_obs", "_sim")
    )

    time = merged_df[time_column]
    observed = merged_df[f"{column_name}_obs"]
    simulated = merged_df[f"{column_name}_sim"]

    plt.figure(figsize=(10, 6))
    plt.plot(time, observed, label="Observed", color="blue")
    plt.plot(time, simulated, label="Simulated", color="red", linestyle="--")
    plt.xlabel("Time")
    plt.ylabel(column_name)
    plt.title(f"Time Series of {column_name}")
    plt.legend()
    plt.grid(True)
    plt.show()
