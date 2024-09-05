"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-22 14:55:56
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-08-29 09:57:50
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_loader.py
Description: 
"""

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
import xarray as xr
from hydroevaluate.dataloader.data_reader import read_training_data
from hydroevaluate.dataloader.data_source import SelfMadeHydroDatasetForEval
from hydroevaluate.utils.heutils import fill_gaps_da, warn_if_nan
from hydroevaluate.dataloader.data_processor import DapengScalerForEval
from hydroevaluate.configs.config import DATE_FORMATS


def detect_date_format(date_str):
    for date_format in DATE_FORMATS:
        try:
            datetime.strptime(date_str, date_format)
            return date_format
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")


class HydroMeanDatasetForEval:
    """This dataset is different from the typical dataset in torch, as it is only used for inference and evaluation."""

    def __init__(self, data_cfg):
        self.data_cfg = data_cfg
        self.data_source = SelfMadeHydroDatasetForEval(data_cfg["data_dir"])
        self._load_data()

    @property
    def ngrid(self):
        return len(self.data_cfg["basin_ids"])

    @property
    def nt(self):
        """length of longest time series in all basins

        Returns
        -------
        int
            number of longest time steps
        """
        if isinstance(self.data_cfg["time_range"][0], list or tuple):
            trange_type_num = len(self.data_cfg["time_range"])
            if trange_type_num not in [self.ngrid, 1]:
                raise ValueError(
                    "The number of time ranges should be equal to the number of basins "
                    "if you choose different time ranges for different basins"
                )
            earliest_date = None
            latest_date = None
            for start_date_str, end_date_str in self.data_cfg["time_range"]:
                date_format = detect_date_format(start_date_str)

                start_date = datetime.strptime(start_date_str, date_format)
                end_date = datetime.strptime(end_date_str, date_format)

                if earliest_date is None or start_date < earliest_date:
                    earliest_date = start_date
                if latest_date is None or end_date > latest_date:
                    latest_date = end_date
            earliest_date = earliest_date.strftime(date_format)
            latest_date = latest_date.strftime(date_format)
        else:
            trange_type_num = 1
            earliest_date = self.data_cfg["time_range"][0]
            latest_date = self.data_cfg["time_range"][1]
        min_time_unit = self.data_cfg["data_unit"][0]
        s_date = pd.to_datetime(earliest_date)
        e_date = pd.to_datetime(latest_date)
        time_series = pd.date_range(start=s_date, end=e_date, freq=min_time_unit)
        return len(time_series)

    def _load_data(self):
        self._read_xc()
        # normalization
        norm_x, norm_c = self._normalize()
        self.x, self.c = self._kill_nan(norm_x, norm_c)
        self._trans2nparr()
        self._create_lookup_table()

    def _read_ts(self):
        gage_id_lst = self.data_cfg["basin_ids"]
        var_lst = self.data_cfg["var_lst"]
        t_range = self.data_cfg["time_range"]
        time_unit = self.data_cfg["data_unit"][0]  # TODO: support multiple time units
        interval = self.data_cfg["interval"]

        subset_list = []
        for start_date, end_date in t_range:
            adjusted_end_date = (
                datetime.strptime(end_date, "%Y-%m-%d-%H") + timedelta(hours=interval)
            ).strftime("%Y-%m-%d-%H")
            subset = self.data_source.read_ts_xrdataset(
                gage_id_lst,
                t_range=[start_date, adjusted_end_date],
                var_lst=var_lst,
                time_units=[time_unit],
            )
            subset_list.append(subset[time_unit])
        return xr.concat(subset_list, dim="time")

    def _trans2da_and_setunits(self, ds):
        """Set units for dataarray transfromed from dataset"""
        result = ds.to_array(dim="variable")
        units_dict = {
            var: ds[var].attrs["units"]
            for var in ds.variables
            if "units" in ds[var].attrs
        }
        result.attrs["units"] = units_dict
        return result

    def _read_xc(self):
        data_forcing_ds = self._read_ts()
        if data_forcing_ds is not None:
            x_origin = self._trans2da_and_setunits(data_forcing_ds)
        else:
            x_origin = None

        if self.data_cfg["constant_vars"]:
            data_attr_ds = self.data_source.read_attr_xrdataset(
                self.data_cfg["basin_ids"],
                self.data_cfg["constant_vars"],
                # self.data_cfg["source_cfgs"]["source_path"]["attributes"],
            )
            c_origin = self._trans2da_and_setunits(data_attr_ds)
        else:
            c_origin = None

        self.x_origin, self.c_origin = x_origin, c_origin

    def _kill_nan(self, x, c):
        x_rm_nan = self.data_cfg["relevant_rm_nan"]
        c_rm_nan = self.data_cfg["constant_rm_nan"]
        if x_rm_nan:
            # As input, we cannot have NaN values
            fill_gaps_da(x, fill_nan="interpolate")
            warn_if_nan(x)
        if c_rm_nan:
            fill_gaps_da(c, fill_nan="mean")
            warn_if_nan(c)
        warn_if_nan(x, nan_mode="all")
        warn_if_nan(c, nan_mode="all")
        return x, c

    def _normalize(self):
        data_source = SelfMadeHydroDatasetForEval(self.data_cfg["data_dir"])
        gamma_norm_cols = self.data_cfg["scaler_params"]["gamma_norm_cols"]
        prcp_norm_cols = self.data_cfg["scaler_params"]["prcp_norm_cols"]
        pbm_norm = self.data_cfg["scaler_params"]["pbm_norm"]
        self.scaler = DapengScalerForEval(
            relevant_vars=self.x_origin,
            constant_vars=self.c_origin,
            data_cfg=self.data_cfg,
            prcp_norm_cols=prcp_norm_cols,
            gamma_norm_cols=gamma_norm_cols,
            pbm_norm=pbm_norm,
            data_source=data_source,
        )
        x, c = self.scaler.load_data()
        return x, c

    def denormalize(self, output):
        # TODO: make it more general
        selected_time_points = pd.date_range(
            start=self.data_cfg["time_range"][0],
            end=self.data_cfg["time_range"][1],
            freq=self.data_cfg["data_unit"],
        )
        coords = {
            "basin_id": self.data_cfg["basin_ids"],
            "time": selected_time_points,
        }

        return self.scaler.inverse_transform(
            xr.DataArray(
                output.transpose(2, 0, 1),
                dims=self.data_cfg["output_vars"],
                coords=coords,
            )
        )

    def _trans2nparr(self):
        """To make __getitem__ more efficient,
        we transform x, y, c to numpy array with shape (nsample, nt, nvar)
        """
        self.x = self.x.transpose("basin", "time", "variable").to_numpy()
        if self.c is not None and self.c.shape[-1] > 0:
            self.c = self.c.transpose("basin", "variable").to_numpy()
            self.c_origin = self.c_origin.transpose("basin", "variable").to_numpy()
        self.x_origin = self.x_origin.transpose("basin", "time", "variable").to_numpy()

    def _create_lookup_table(self):
        lookup = []
        # list to collect basins ids of basins without a single training sample
        basin_coordinates = len(self.data_cfg["basin_ids"])
        rho = self.data_cfg["rho"]
        warmup_length = self.data_cfg["warmup_length"]
        horizon = self.data_cfg["horizon"]
        max_time_length = self.nt
        for basin in tqdm(range(basin_coordinates), file=sys.stdout, disable=False):
            lookup.extend(
                (basin, f)
                for f in range(warmup_length, max_time_length - rho - horizon + 1)
            )
        self.lookup_table = dict(enumerate(lookup))
        self.num_samples = len(self.lookup_table)
