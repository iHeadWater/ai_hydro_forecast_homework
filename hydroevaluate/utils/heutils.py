"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2024-05-31 13:35:19
LastEditors: Wenyu Ouyang
Description: some common functions
FilePath: \\hydroevaluate\\hydroevaluate\\utils\\heutils.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from collections import OrderedDict
from typing import Optional
import warnings
from matplotlib import pyplot as plt
import numpy as np
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


def _trans_norm(
    x: xr.DataArray,
    var_lst: list,
    stat_dict: dict,
    log_norm_cols: list = None,
    to_norm: bool = True,
    **kwargs,
) -> np.array:
    """
    Normalization or inverse normalization

    There are two normalization formulas:

    .. math:: normalized_x = (x - mean) / std

    and

     .. math:: normalized_x = [log_{10}(\sqrt{x} + 0.1) - mean] / std

     The later is only for vars in log_norm_cols; mean is mean value; std means standard deviation

    Parameters
    ----------
    x
        data to be normalized or denormalized
    var_lst
        the type of variables
    stat_dict
        statistics of all variables
    log_norm_cols
        which cols use the second norm method
    to_norm
        if true, normalize; else denormalize

    Returns
    -------
    np.array
        normalized or denormalized data
    """
    if x is None:
        return None
    if log_norm_cols is None:
        log_norm_cols = []
    if type(var_lst) is str:
        var_lst = [var_lst]
    out = xr.full_like(x, np.nan)
    for item in var_lst:
        stat = stat_dict[item]
        if to_norm:
            out.loc[dict(variable=item)] = (
                (np.log10(np.sqrt(np.abs(x.sel(variable=item))) + 0.1) - stat[2])
                / stat[3]
                if item in log_norm_cols
                else (x.sel(variable=item) - stat[2]) / stat[3]
            )
        elif item in log_norm_cols:
            out.loc[dict(variable=item)] = (
                np.power(10, x.sel(variable=item) * stat[3] + stat[2]) - 0.1
            ) ** 2
        else:
            out.loc[dict(variable=item)] = x.sel(variable=item) * stat[3] + stat[2]
    if to_norm:
        # after normalization, all units are dimensionless
        out.attrs = {}
    elif "recover_units" in kwargs and kwargs["recover_units"] is not None:
        recover_units = kwargs["recover_units"]
        for item in var_lst:
            out.attrs["units"][item] = recover_units[item]
    return out


def _prcp_norm(x: np.array, mean_prep: np.array, to_norm: bool) -> np.array:
    """
    Normalize or denormalize data with mean precipitation.

    The formula is as follows when normalizing (denormalize equation is its inversion):

    .. math:: normalized_x = \frac{x}{precipitation}

    Parameters
    ----------
    x
        data to be normalized or denormalized
    mean_prep
        basins' mean precipitation
    to_norm
        if true, normalize; else denormalize

    Returns
    -------
    np.array
        normalized or denormalized data
    """
    tempprep = np.tile(mean_prep, (1, x.shape[1]))
    return x / tempprep if to_norm else x * tempprep


def wrap_t_s_dict(data_cfgs: dict) -> OrderedDict:
    """
    Basins and periods

    Parameters
    ----------

    data_cfgs
        configs for reading from data source
    is_tra_val_te
        train, valid or test

    Returns
    -------
    OrderedDict
        OrderedDict(sites_id=basins_id, t_final_range=t_range_list)
    """
    basins_id = data_cfgs["basin_ids"]
    if "time_range" in data_cfgs:
        t_range_list = data_cfgs["time_range"]
    else:
        raise ValueError(
            f"Error! time_range is not specified in data_cfgs: {data_cfgs}"
        )
    return OrderedDict(sites_id=basins_id, t_final_range=t_range_list)


def fill_gaps_da(da: xr.DataArray, fill_nan: Optional[str] = None) -> xr.DataArray:
    """Fill gaps in a DataArray"""
    if fill_nan is None or da is None:
        return da
    assert isinstance(da, xr.DataArray), "Expect da to be DataArray (not dataset)"
    # fill gaps
    if fill_nan == "et_ssm_ignore":
        all_non_nan_idx = []
        for i in range(da.shape[0]):
            non_nan_idx_tmp = np.where(~np.isnan(da[i].values))
            all_non_nan_idx = all_non_nan_idx + non_nan_idx_tmp[0].tolist()
        # some NaN data appear in different dates in different basins
        non_nan_idx = np.unique(all_non_nan_idx).tolist()
        for i in range(da.shape[0]):
            targ_i = da[i][non_nan_idx]
            da[i][non_nan_idx] = targ_i.interpolate_na(
                dim="time", fill_value="extrapolate"
            )
    elif fill_nan == "mean":
        # fill with mean
        for var in da["variable"].values:
            var_data = da.sel(variable=var)  # select the data for the current variable
            mean_val = var_data.mean(
                dim="basin"
            )  # calculate the mean across all basins
            if warn_if_nan(mean_val):
                # when all value are NaN, mean_val will be NaN, we set mean_val to -1
                mean_val = -1
            filled_data = var_data.fillna(
                mean_val
            )  # fill NaN values with the calculated mean
            da.loc[dict(variable=var)] = (
                filled_data  # update the original dataarray with the filled data
            )
    elif fill_nan == "interpolate":
        # fill interpolation
        for i in range(da.shape[0]):
            da[i] = da[i].interpolate_na(dim="time", fill_value="extrapolate")
    else:
        raise NotImplementedError(f"fill_nan {fill_nan} not implemented")
    return da


def warn_if_nan(dataarray, max_display=5, nan_mode="any"):
    """
    Issue a warning if the dataarray contains any NaN values and display their locations.

    Parameters
    -----------
    dataarray: xr.DataArray
        Input dataarray to check for NaN values.
    max_display: int
        Maximum number of NaN locations to display in the warning.
    nan_mode: str
        Mode of NaN checking: 'any' for any NaNs, 'all' for all values being NaNs.
    """
    if nan_mode not in ["any", "all"]:
        raise ValueError("nan_mode must be 'any' or 'all'")

    if nan_mode == "all" and np.all(np.isnan(dataarray.values)):
        raise ValueError("The dataarray contains only NaN values!")

    nan_indices = np.argwhere(np.isnan(dataarray.values))
    total_nans = len(nan_indices)

    if total_nans <= 0:
        return False
    message = f"The dataarray contains {total_nans} NaN values!"

    # Displaying only the first few NaN locations if there are too many
    display_indices = nan_indices[:max_display].tolist()
    message += (
        f" Here are the indices of the first {max_display} NaNs: {display_indices}..."
        if total_nans > max_display
        else f" Here are the indices of the NaNs: {display_indices}"
    )
    warnings.warn(message)

    return True


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
                    var_data = xr.DataArray(
                        var_data_m3s, coords=var_data.coords, dims=var_data.dims
                    )
                # Convert flow from m^3/s to mm/h
                data[var_name] = (var_data / area) * 3.6
            else:
                # Handle other unit conversions
                quantity = var_data.values * ureg(from_unit)
                converted_quantity = quantity.to(to_unit).magnitude
                data[var_name] = xr.DataArray(
                    converted_quantity, coords=var_data.coords, dims=var_data.dims
                )
    return data


def read_yaml(version):
    cfg_path = os.path.join(work_dir, f"test_data/aiff_cfg/aiff_v{str(version)}.yml")
    if not os.path.exists(cfg_path):
        version_url = f"https://raw.githubusercontent.com/iHeadWater/AIFloodForecast/main/scripts/conf/v{str(version)}.yml"
        yml_str = ur.request("GET", version_url).data.decode("utf8")
    else:
        with open(cfg_path, "r") as fp:
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
    return 1 - (numerator / denominator)  # NSE


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
