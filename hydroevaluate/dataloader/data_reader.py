"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 09:49:24
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-03 15:23:59
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_reader.py
Description:
"""

import pandas as pd
import os
import xarray as xr

from hydroevaluate.utils.heutils import convert_units
from hydrodatasource.reader.data_source import SelfMadeHydroDataset


def read_selfmade_data(
    data_dir,
    object_ids,
    var_lst=None,
    time_unit=None,
    prefix=None,
    postfix=None,
):
    """
    read data for model input or evaluation, we only support a demo for reading data
    modify it yourself if neccessary

    Parameters
    ----------
    data_dir : _type_
        _description_
    object_ids : _type_
        _description_
    time_unit : _type_, optional
        _description_, by default None

    Returns
    -------
    xr.Dataset
    """
    prefix = prefix + "_" if prefix is not None else ""
    postfix = "_" + postfix if postfix is not None else ""
    if data_dir.endswith(".nc"):
        nc_data_path = data_dir
        xr_dataset = xr.open_dataset(nc_data_path)
        xr_dataset = xr_dataset.sel(basin=object_ids)
    else:
        all_dataarrays = []
        for basin_id in object_ids:
            csv_data_path = os.path.join(data_dir, f"{prefix}{basin_id}{postfix}.csv")
            txt_data_path = os.path.join(data_dir, f"{prefix}{basin_id}{postfix}.txt")
            if os.path.exists(csv_data_path):
                df_data = pd.read_csv(csv_data_path)
            elif os.path.exists(txt_data_path):
                df_data = pd.read_csv(txt_data_path)
            else:
                raise ValueError(f"Cannot find data for basin_id {basin_id}")
            df_data["basin_id"] = basin_id
            df_data.set_index(["time", "basin_id"], inplace=True)
            xr_dataarray = df_data.to_xarray()
            all_dataarrays.append(xr_dataarray)
        xr_dataset = xr.concat(all_dataarrays, dim="basin_id")

    if var_lst is not None:
        if var_lst not in xr_dataset.data_vars:
            raise ValueError("Variable not supported")
        xr_dataset = xr_dataset[var_lst]
    # Column renaming and unit conversion
    if time_unit is not None:
        xr_dataset = convert_units(xr_dataset, time_unit)

    return xr_dataset


# TODO: create a hydrodataset for eval or infer, we do not need all functions in SelfMadeHydroDataset, and it may cause error in FAPP
def read_training_data(
    data_dir, object_ids, var_lst, t_range_test=None, time_unit=None
):
    if time_unit is None:
        time_unit = ["1D"]
    dataset = SelfMadeHydroDataset(data_path=data_dir, time_unit=time_unit)
    return dataset.read_ts_xrdataset(
        gage_id_lst=object_ids,
        t_range=t_range_test,
        var_lst=var_lst,
        time_units=time_unit,
    )[time_unit[0]]
