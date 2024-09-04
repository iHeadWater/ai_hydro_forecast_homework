"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-22 14:55:56
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-08-29 09:57:50
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_loader.py
Description: 
"""

# -*- coding: utf-8 -*-
from hydroevaluate.dataloader.data_reader import read_selfmade_data, read_training_data
from hydroevaluate.utils.heutils import fill_gaps_da, warn_if_nan


class DataLoader:
    """This dataset is different from the typical dataset in torch, as it is only used for inference and evaluation."""

    def __init__(self, data_cfgs):
        self.data_cfgs = data_cfgs

    def load_data(self):
        self._read_xc()
        # normalization
        norm_x, norm_c = self._normalize()
        self.x, self.c = self._kill_nan(norm_x, norm_c)
        return self.x, self.c

    def _read_xc(self):
        data_dir = self.data_cfgs["data_dir"]
        basin_ids = self.data_cfgs["basin_ids"]
        var_lst = self.data_cfgs["var_lst"]
        time_range = self.data_cfgs["time_range"]
        time_unit = self.data_cfgs["time_unit"]
        return read_training_data(data_dir, basin_ids, var_lst, time_range, time_unit)

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
        pass

    def denormalize(self):
        pass
