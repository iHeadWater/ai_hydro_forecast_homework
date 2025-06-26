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
import torch
from tqdm import tqdm
import xarray as xr
from hydrodatasource.reader.data_source import SelfMadeHydroDataset
from hydroevaluate.utils.heutils import fill_gaps_da, warn_if_nan, wrap_t_s_dict
from hydroevaluate.dataloader.data_processor import DapengScalerForEval
from hydroevaluate.configs.config import DATE_FORMATS
from torchhydro.datasets.data_sets import Seq2SeqDataset


class Seq2SeqDatasetForEval(Seq2SeqDataset):
    """This dataset is different from the typical dataset in torch, as it is only used for inference and evaluation."""

    def __init__(self, data_cfgs, data_source=None):
        self.data_cfgs = data_cfgs
        self._data_source = data_source or self.initialize_data_source()
        super(Seq2SeqDatasetForEval, self).__init__(data_cfgs, is_tra_val_te="valid")
        self.train_mode = False

    def initialize_data_source(self):
        """Initialize default data source based on configuration."""
        interval = self.data_cfgs["min_time_interval"]
        unit = self.data_cfgs["min_time_unit"]
        time_unit = f"{interval}{unit}"
        return SelfMadeHydroDataset(
            self.data_cfgs["data_dir"],
            time_unit=[time_unit],
        )

    @property
    def data_source(self):
        return self._data_source

    @property
    def ngrid(self):
        return len(self.data_cfgs["object_ids"])

    @property
    def category_to_index(self):
        unique_categories = []
        for config in self.data_cfgs["feature_mapping"].values():
            if config["category"] not in unique_categories:
                unique_categories.append(config["category"])
        return {category: idx for idx, category in enumerate(unique_categories)}

    def _pre_load_data(self):
        self.t_s_dict = wrap_t_s_dict(self.data_cfgs)
        self.rho = self.data_cfgs["rho"]
        self.warmup_length = self.data_cfgs["warmup_length"]
        self.horizon = self.data_cfgs["horizon"]

    def _load_data(self):
        self._pre_load_data()
        self._read_xc()
        # normalization
        norm_x, norm_c = self._normalize()
        self.x, self.c = self._kill_nan(norm_x, norm_c)
        self._trans2nparr()
        self._create_lookup_table()

    def _read_ts(self):
        gage_id_lst = self.data_cfgs["object_ids"]
        var_lst = self.data_cfgs["var_lst"]
        t_range = self.data_cfgs["t_range_test"]
        interval = self.data_cfgs["min_time_interval"]
        unit = self.data_cfgs["min_time_unit"]
        time_unit = f"{interval}{unit}"

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

    def _read_xc(self):
        data_forcing_ds = self._read_ts()
        if data_forcing_ds is not None:
            x_origin = self._trans2da_and_setunits(data_forcing_ds)
        else:
            x_origin = None

        # temp use
        x_origin[0] = x_origin[0] * 1
        if self.data_cfgs["constant_vars"]:
            data_attr_ds = self.data_source.read_attr_xrdataset(
                self.data_cfgs["object_ids"],
                self.data_cfgs["constant_vars"],
                # self.data_cfgs["source_cfgs"]["source_path"]["attributes"],
            )
            c_origin = self._trans2da_and_setunits(data_attr_ds)
        else:
            c_origin = None

        self.x_origin, self.c_origin = x_origin, c_origin

    def _kill_nan(self, x, c):
        x_rm_nan = self.data_cfgs["relevant_rm_nan"]
        c_rm_nan = self.data_cfgs["constant_rm_nan"]
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
        gamma_norm_cols = self.data_cfgs["scaler_params"]["gamma_norm_cols"]
        prcp_norm_cols = self.data_cfgs["scaler_params"]["prcp_norm_cols"]
        pbm_norm = self.data_cfgs["scaler_params"]["pbm_norm"]
        self.scaler = DapengScalerForEval(
            relevant_vars=self.x_origin,
            constant_vars=self.c_origin,
            data_cfgs=self.data_cfgs,
            prcp_norm_cols=prcp_norm_cols,
            gamma_norm_cols=gamma_norm_cols,
            pbm_norm=pbm_norm,
            data_source=self.data_source,
        )
        x, c = self.scaler.load_data()
        return x, c

    def denormalize(self, output):
        # TODO: make it more general
        prec_window = self.data_cfgs["prec_window"]
        selected_time_points = self.times[0][self.data_cfgs["rho"] - prec_window :]
        self.data_cfgs["target_cols"] = self.data_cfgs["target_cols"]
        dims = ["variable", "basin", "time"]
        coords = {
            "variable": self.data_cfgs["target_cols"],
            "basin": self.data_cfgs["object_ids"],
            "time": selected_time_points,
        }

        return self.scaler.inverse_transform(
            xr.DataArray(
                output.transpose(2, 0, 1),
                dims=dims,
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
        basin_coordinates = len(self.data_cfgs["object_ids"])
        rho = self.data_cfgs["rho"]
        warmup_length = self.data_cfgs["warmup_length"]
        horizon = self.data_cfgs["horizon"]
        max_time_length = self.nt
        for basin in tqdm(range(basin_coordinates), file=sys.stdout, disable=False):
            lookup.extend(
                (basin, f)
                for f in range(warmup_length, max_time_length - rho - horizon + 1)
            )
        self.lookup_table = dict(enumerate(lookup))
        self.num_samples = len(self.lookup_table)

    def __getitem__(self, item: int):
        basin, idx = self.lookup_table[item]
        feature_mapping = self.data_cfgs["feature_mapping"]
        rho = self.rho
        horizon = self.horizon

        # 提取整个时间段的数据
        seq_input = self.x[basin, idx:, :]  # shape: (seq_length, feature)

        # 初始化存储结果的字典，基于类别
        result = {idx: [] for idx in self.category_to_index.values()}

        # 动态生成时间范围
        time_ranges = []
        for config in feature_mapping.values():
            time_ranges.extend(config["time_ranges"])

        max_time = max(
            end
            for feature in feature_mapping.values()
            for _, end in feature["time_ranges"]
        )

        x = np.zeros((max_time, len(self.category_to_index)))

        for i, (feature, info) in enumerate(feature_mapping.items()):
            category = info["category"]
            time_ranges = info["time_ranges"]
            category_index = self.category_to_index[category]

            for start, end in time_ranges:
                x[start:end, category_index] += seq_input[start:end, i]

        c = self.c[basin, :]
        c = np.tile(c, (rho + horizon, 1))
        features_only_rho = [
            self.category_to_index[category]
            for category in self.data_cfgs["features_only_rho"]
            if category in self.category_to_index
        ]
        x_r = np.concatenate((x[:rho], c[:rho]), axis=1)
        x_h = np.concatenate((x[rho : rho + horizon], c[rho:]), axis=1)
        x_h = np.delete(x_h, features_only_rho, axis=1)

        return [
            torch.from_numpy(x_r).float(),
            torch.from_numpy(x_h).float(),
        ]


class SeqForecastDatasetForEval(Seq2SeqDatasetForEval):
    def __getitem__(self, item: int):
        basin, time = self.lookup_table[item]
        rho = self.rho  # forecast history
        horizon = self.horizon  # forecast length
        # p cover all encoder-decoder periods; +1 means the period while +0 means start of the current period
        p = self.x[basin, time : time + rho + horizon, 0].reshape(-1, 1)
        # se only cover encoder periods
        se = self.x[basin, time : time + rho, 1:]
        # se only cover decoder periods
        sd = self.x[basin, time + rho : time + rho + horizon, 1:]
        # encoder dynamic features
        xe = np.concatenate((p[:rho], se), axis=1)
        # encoder static features
        if self.c is None or self.c.shape[-1] == 0:
            xec = xe
        else:
            c = self.c[basin, :]
            # c = np.tile(c, (rho + horizon, 1))
            # xec = c[:rho]
            xec = c
        # xh cover decoder periods
        xd = np.concatenate((p[rho:], sd), axis=1)
        # decoder static features
        xec = c
        xdc = c

        return [
            torch.from_numpy(xe).float(),
            torch.from_numpy(xec).float(),
            torch.from_numpy(xd).float(),
            torch.from_numpy(xdc).float(),
        ]
