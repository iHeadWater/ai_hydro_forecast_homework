"""
Author: Wenyu Ouyang
Date: 2025-01-11 21:07:20
LastEditTime: 2025-01-12 17:37:58
LastEditors: Wenyu Ouyang
Description: dataloader for model evaluation
FilePath: \hydroevaluate\hydroevaluate\dataloader\hydrodataloader.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
from torchhydro.datasets.data_sources import data_sources_dict


class HydroDataLoader(ABC):
    def __init__(self, data_cfgs=None):
        """We use a hydrodataloader to load tensor data for model evaluation
        It needs a configuration file to specify the variables and its corresponding parameters, such as the time range
        TODO: We need to implement the dataloader function to load the data

        Parameters
        ----------
        conf_file : _type_, optional
            _description_, by default None
        """
        self.data_cfgs = data_cfgs

    @abstractmethod
    def load_input(self):
        pass


class DataloaderForHydroModel(HydroDataLoader):
    def __init__(self, data_cfgs):
        super().__init__()
        self.data_cfgs = data_cfgs
        source_name = self.data_cfgs["source_cfgs"]["source_name"]
        source_path = self.data_cfgs["source_cfgs"]["source_path"]
        other_settings = self.data_cfgs["source_cfgs"].get("other_settings", {})
        self.data_source = data_sources_dict[source_name](source_path, **other_settings)
        self.time_unit = (
            str(data_cfgs["min_time_interval"]) + data_cfgs["min_time_unit"]
        )

    @property
    def prcp_col(self):
        return self.data_cfgs["relevant_cols"][0]

    @property
    def pet_col(self):
        return self.data_cfgs["relevant_cols"][1]

    def load_input(self, gage_id_lst):
        time_range = self.data_cfgs["t_range_test"]
        var_lst = self.data_cfgs["relevant_cols"]
        ds = self.data_source.read_ts_xrdataset(gage_id_lst, time_range, var_lst)[
            self.time_unit
        ]
        p_and_e_dict = {}
        for gage_id in gage_id_lst:
            ds_gage = ds.sel(basin=gage_id)
            warmup = self.data_cfgs["warmup_length"]
            rho = self.data_cfgs["hindcast_length"]
            horizon = self.data_cfgs["forecast_length"]
            full_length = warmup + rho + horizon
            dataframes = []

            for i in range(0, len(ds_gage.time), horizon):
                if i + full_length > len(ds_gage.time):
                    break

                time_segment = ds_gage.time[i : i + full_length].values

                prcp = (
                    ds_gage[self.prcp_col]
                    .isel(time=slice(i, i + full_length))
                    .values.flatten()
                )

                basin_values = [gage_id] * len(time_segment)
                pet = (
                    ds_gage[self.pet_col]
                    .isel(time=slice(i, i + full_length))
                    .values.flatten()
                )

                df = pd.DataFrame(
                    {
                        "time": time_segment,
                        "prcp": prcp,
                        "pet": pet,
                        "basin": basin_values,
                    }
                )
                dataframes.append(df)
            p_and_e_dict[gage_id] = dataframes
        return p_and_e_dict
