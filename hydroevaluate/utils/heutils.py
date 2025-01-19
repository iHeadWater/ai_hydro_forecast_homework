"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2025-01-19 14:22:56
LastEditors: Wenyu Ouyang
Description: some common functions
FilePath: \hydroevaluate\hydroevaluate\utils\heutils.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import pint
import datetime
import numpy as np
import pandas as pd
import xarray as xr

from hydroutils.hydro_stat import stat_error_i

ureg = pint.UnitRegistry()
ureg.setup_matplotlib()



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


def calculate_metrics(observed_file_path, simulated_file_path, var_name, metrics=None):
    """
    Calculate multiple metrics (NSE, RMSE, R2, KGE, FHV, FLV) between observed and simulated data.

    Parameters
    ----------
    observed_file_path : str
        Path of observed data file (CSV or NetCDF).
    simulated_file_path : str
        Path of simulated data file (CSV or NetCDF).
    var_name : str
        The name of the variable (column for CSV or variable for NetCDF).
    metrics : list of str, optional
        List of metrics to calculate (default is all available metrics).

    Returns
    -------
    dict : {metric_name: metric_value}
        Dictionary containing the calculated metrics.

    Raises
    ------
    ValueError
        If the file type is unsupported or the necessary columns/variables are not found.
    """
    # Check if the metrics parameter is provided, else use all available metrics
    if metrics is None:
        metrics = ["NSE", "RMSE", "Corr", "KGE", "FHV", "FLV"]

    # Load the data
    observed, simulated = load_data(observed_file_path, simulated_file_path, var_name)
    valid_mask = ~np.isnan(observed) & ~np.isnan(simulated)
    observed = observed[valid_mask]
    simulated = simulated[valid_mask]
    # Calculate the metrics
    results_ = stat_error_i(observed, simulated)
    # choose the metrics
    results = {metric: results_[metric] for metric in metrics}
    return results


def load_data(observed_file_path, simulated_file_path, var_name):
    """
    Load observed and simulated data from CSV or NetCDF files.

    Parameters
    ----------
    observed_file_path : str
        Path to the observed data file.
    simulated_file_path : str
        Path to the simulated data file.
    var_name : str
        The name of the variable to extract.

    Returns
    -------
    observed : numpy.ndarray
        Observed values for the variable.
    simulated : numpy.ndarray
        Simulated values for the variable.
    """
    if isinstance(observed_file_path, str) and isinstance(simulated_file_path, str):
        if observed_file_path.endswith(".csv") and simulated_file_path.endswith(".csv"):
            observed_df = pd.read_csv(observed_file_path)
            simulated_df = pd.read_csv(simulated_file_path)

            # Merge dataframes on 'time' column
            time_column = "time" if "time" in observed_df.columns else "time_start"
            observed_df[time_column] = pd.to_datetime(observed_df[time_column])
            simulated_df[time_column] = pd.to_datetime(simulated_df[time_column])
            merged_df = pd.merge(
                observed_df, simulated_df, on=time_column, suffixes=("_obs", "_sim")
            )

            observed = merged_df[f"{var_name}_obs"].values
            simulated = merged_df[f"{var_name}_sim"].values

        elif observed_file_path.endswith(".nc") and simulated_file_path.endswith(".nc"):
            observed_ds = xr.open_dataset(observed_file_path)
            simulated_ds = xr.open_dataset(simulated_file_path)

            # Get variable data
            observed = observed_ds[var_name].values
            simulated = simulated_ds[var_name].values

    elif isinstance(observed_file_path, xr.Dataset) and isinstance(
        simulated_file_path, xr.Dataset
    ):
        observed_ds = observed_file_path
        simulated_ds = simulated_file_path

        # Get variable data
        observed = observed_ds[var_name].values
        simulated = simulated_ds[var_name].values
    elif isinstance(observed_file_path, pd.DataFrame) and isinstance(
        simulated_file_path, pd.DataFrame
    ):
        observed = observed_file_path[var_name].values
        simulated = simulated_file_path[var_name].values

    return observed, simulated
