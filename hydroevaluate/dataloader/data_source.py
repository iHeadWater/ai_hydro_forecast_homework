"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-30 15:44:29
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-30 15:44:41
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_source.py
Description: 
"""

from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
import tqdm
import xarray as xr
import os
import re
from hydroutils import hydro_file
from hydrodatasource.reader.data_source import SelfMadeHydroDataset

CACHE_DIR = hydro_file.get_cache_dir()


class CustomDataSourceForTorchHydro:
    """
    This part is for selfmade data source, you need to implement the functions below.
    Here is an example when you use your own data_source:
        class MyDataSource(CustomDataSourceForTorchHydro):
            def __init__(self):
                super().__init__()
            def read_ts_xrdataset(self):
                ...
            def read_attr_xrdataset(self):
                ...
            def read_mean_prcp(self):
                ...
            def other_function(self):
                <if you need>
        data_source = CustomDataSourceForTorchHydro()
        eval_deep_hydro = EvalDeepHydro(DEFAULT_cfgs, data_source=data_source)
        eval_deep_hydro.model_infer()
    """

    def __init__(self):
        pass

    def read_ts_xrdataset(self, gage_id_lst, t_range, var_lst, time_units):
        """
        Returns a dictionary with time units as keys and xarray.Dataset as values.

        The structure of the returned dictionary is similar to below:

        {
            'time_unit': <xarray.Dataset>,
            ...
        }

        - 'time_unit': A string representing the time interval (e.g., '3h', '1h').
        - <xarray.Dataset>: An xarray Dataset object with the following structure:
            - Dimensions:
                * basin: represents different basin IDs (e.g., 'AAAA').
                * time: represents time steps, typically datetime64 format.
            - Coordinates:
                * basin (basin): A list of basin identifiers.
                * time (time): A list of time values in datetime64[ns].
            - Data variables:
                * total_precipitation_hourly (basin, time)
                * precipitationCal (basin, time)
                * hourly_precipitation (basin, time)
                * sm_surface (basin, time)

        Example of a dataset within the dictionary:

        <xarray.Dataset>
        Dimensions:  (basin: 2, time: 490)
        Coordinates:
        * basin    (basin) <U17 'AAAA' 'BBBB'
        * time     (time) datetime64[ns] 2015-06-01T01:00:00 2015-06-01T04:00:00 ... 2015-06-01T10:00:00
        Data variables:
            total_precipitation_hourly  (basin, time) float64 0.01 ... 0.4
            precipitationCal            (basin, time) float64 0.01 ... 0.4
            hourly_precipitation        (basin, time) float64 0.01 ... 0.4
            sm_surface                  (basin, time) float64 0.01 ... 0.4

        Returns:
            dict: A dictionary where the keys are time intervals (e.g., '3h') and values are xarray.Dataset objects.
        """
        raise NotImplementedError

    def read_attr_xrdataset(self, gage_id_lst, var_lst):
        """
        Returns an xarray.Dataset with basin-level variables.

        The dataset contains the following structure:

        - Dimensions:
        * basin: Represents the basin identifiers, with a total of 2 basins. The basin identifiers are strings up to 25 characters long (e.g., 'songliao_21401050', 'songliao_21401550').

        - Coordinates:
        * basin (basin): A list of basin identifiers, represented as strings with a maximum length of 25 characters.

        - Data variables:
        * area (basin): The area of each basin, represented as float64.
        ...

        Returns:
            xarray.Dataset: A dataset containing basin-level environmental and geographical variables.
        """
        raise NotImplementedError

    def read_mean_prcp(self, gage_id_lst):
        """
        the pre_mm_syr variable in attr

        <xarray.Dataset> Size: 216B
        Dimensions:     (basin: 2)
        Coordinates:
        * basin       (basin) <U25 200B 'AAAA' 'BBBB'
        Data variables:
            pre_mm_syr  (basin) float64 16B ...
        """
        # return self.read_attr_xrdataset(gage_id_lst, ["pre_mm_syr"])
        raise NotImplementedError


class CustomDataSourceForHydroModel:
    """
    For Xaj Model
    """

    def __init__(self):
        pass

    def get_p_and_e_dict(self, gage_id_lst):
        raise NotImplementedError


class StandardDataSourceForHydroModel(CustomDataSourceForHydroModel):
    def __init__(self, data_cfgs):
        super().__init__()
        self.data_cfgs = data_cfgs
        self.time_unit = (
            str(data_cfgs["min_time_interval"]) + data_cfgs["min_time_unit"]
        )
        self.temp_datasource = SelfMadeHydroDataset(
            data_path=data_cfgs["data_dir"], time_unit=[self.time_unit]
        )

    def get_p_and_e_dict(self, gage_id_lst):
        time_range = self.data_cfgs["t_range_test"]
        converted_times = [
            [
                datetime.strptime(start, "%Y-%m-%d-%H").strftime("%Y-%m-%d %H:00:00"),
                datetime.strptime(end, "%Y-%m-%d-%H").strftime("%Y-%m-%d %H:00:00"),
            ]
            for start, end in time_range
        ][0]
        var_lst = self.data_cfgs["var_lst"]
        ds = self.temp_datasource.read_ts_xrdataset(
            gage_id_lst, converted_times, var_lst
        )[self.time_unit]
        p_and_e_dict = {}
        for gage_id in gage_id_lst:
            ds_gage = ds.sel(basin=gage_id)
            rho = self.data_cfgs["rho"]
            horizon = self.data_cfgs["horizon"]
            full_length = rho + horizon
            feature_mapping = self.data_cfgs["feature_mapping"]
            pet_data = json.load(
                open(
                    os.path.join(self.data_cfgs["json_folder"], f"{gage_id}.json"), "r"
                )
            )["pets"]
            pet_value_map = {entry["month"]: entry["petValue"] for entry in pet_data}

            dataframes = []

            for i in range(0, len(ds_gage.time), horizon):
                if i + full_length > len(ds_gage.time):
                    break

                time_segment = ds_gage.time[i : i + full_length].values

                rain = []
                for feature, config in feature_mapping.items():
                    for time_range in config["time_ranges"]:
                        start, end = time_range
                        rain.extend(
                            ds_gage[feature]
                            .isel(time=slice(i + start, i + end))
                            .values.flatten()
                            .tolist()
                        )

                rain = rain[:full_length] + [np.nan] * (full_length - len(rain))

                streamflow_values = (
                    ds_gage["streamflow"].isel(time=slice(i, i + rho)).values.flatten()
                )
                streamflow = np.pad(
                    streamflow_values, (0, horizon), constant_values=np.nan
                )

                pet = [
                    pet_value_map.get(pd.Timestamp(t).month, np.nan)
                    for t in time_segment
                ]

                month_values = [pd.Timestamp(t).month for t in time_segment]
                basin_values = [gage_id] * len(time_segment)

                df = pd.DataFrame(
                    {
                        "time": time_segment,
                        "rain": rain,
                        "flow": streamflow,
                        "pet": pet,
                        "month": month_values,
                        "basin": basin_values,
                    }
                )
                dataframes.append(df)
            p_and_e_dict[gage_id] = dataframes
        return p_and_e_dict
