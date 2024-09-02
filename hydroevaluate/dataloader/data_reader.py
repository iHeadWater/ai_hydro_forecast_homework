'''
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 09:49:24
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-08-29 18:42:36
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_reader.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

import pandas as pd
import os
import xarray as xr

from hydroevaluate.utils.heutils import convert_units

def read_selfmade_data(
    data_dir,
    basin_ids,
    data_names=None,
    data_units=None,
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
    basin_ids : _type_
        _description_
    data_names : _type_, optional
        _description_, by default None
    data_units : _type_, optional
        _description_, by default None

    Returns
    -------
    xr.Dataset
    """
    prefix = prefix + '_' if prefix is not None else ''
    postfix = '_' + postfix if postfix is not None else ''
    nc_data_path = os.path.join(data_dir, f'{prefix}{basin_id}{postfix}.nc')
    if os.path.exists(nc_data_path):
        xr_dataset = xr.open_dataset(nc_data_path)
    else:
        all_dataarrays = []
        for basin_id in basin_ids:
            csv_data_path = os.path.join(data_dir, f'{prefix}{basin_id}{postfix}.csv')
            txt_data_path = os.path.join(data_dir, f'{prefix}{basin_id}{postfix}.txt')
            if os.path.exists(csv_data_path):
                df_data = pd.read_csv(csv_data_path)
            elif os.path.exists(txt_data_path):
                df_data = pd.read_csv(txt_data_path)
            else:
                raise ValueError(f'Cannot find data for basin_id {basin_id}')
            df_data['basin_id'] = basin_id
            df_data.set_index(['time', 'basin_id'], inplace=True)
            xr_dataarray = df_data.to_xarray()
            all_dataarrays.append(xr_dataarray)
        xr_dataset = xr.concat(all_dataarrays, dim='basin_id')
            
    # Column renaming and unit conversion
    if data_units is not None:
        xr_dataset = convert_units(xr_dataset, data_units)
    return xr_dataset