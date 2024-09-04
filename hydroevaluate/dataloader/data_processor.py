"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 09:16:19
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-04 14:25:16
FilePath: /hydroevaluate/hydroevaluate/dataloader/agg.py
Description: 
"""

import json
import os
import shutil
import numpy as np
import pandas as pd
from shutil import SameFileError
from hydroevaluate.utils.heutils import (
    _prcp_norm,
    _trans_norm,
    convert_units,
    wrap_t_s_dict,
)


def aggregate_dataframe(df, units):
    # agg_df = convert_units(df, units)
    pass


class DapengScalerForEval(object):
    def __init__(
        self,
        relevant_vars: np.array,
        constant_vars: np.array,
        data_cfg: dict,
        other_vars: dict = None,
        prcp_norm_cols=None,
        gamma_norm_cols=None,
        pbm_norm=False,
        data_source: object = None,
    ):
        """
        The normalization and denormalization methods from Dapeng's 1st WRR paper.
        Some use StandardScaler, and some use special norm methods

        Parameters
        ----------
        target_vars
            output variables
        relevant_vars
            input dynamic variables
        constant_vars
            input static variables
        data_cfg
            data parameter config in data source
        is_tra_val_te
            train/valid/test
        other_vars
            if more input are needed, list them in other_vars
        prcp_norm_cols
            data items which use _prcp_norm method to normalize
        gamma_norm_cols
            data items which use log(\sqrt(x)+.1) method to normalize
        pbm_norm
            if true, use pbm_norm method to normalize; the output of pbms is not normalized data, so its inverse is different.
        """
        if prcp_norm_cols is None:
            prcp_norm_cols = [
                "streamflow",
            ]
        if gamma_norm_cols is None:
            gamma_norm_cols = [
                "total_precipitation_hourly",
                "sm_surface",
            ]
        self.data_forcing = relevant_vars
        self.data_attr = constant_vars
        self.data_cfg = data_cfg
        self.t_s_dict = wrap_t_s_dict(data_cfg)
        self.data_other = other_vars
        self.prcp_norm_cols = prcp_norm_cols
        self.gamma_norm_cols = gamma_norm_cols
        # both prcp_norm_cols and gamma_norm_cols use log(\sqrt(x)+.1) method to normalize
        self.log_norm_cols = gamma_norm_cols + prcp_norm_cols
        self.pbm_norm = pbm_norm
        self.data_source = data_source
        # save stat_dict of training period in test_path for valid/test
        stat_file = data_cfg["stat_file_path"]
        assert os.path.isfile(stat_file)
        with open(stat_file, "r") as fp:
            self.stat_dict = json.load(fp)

    @property
    def mean_prcp(self):
        return (
            self.data_source.read_mean_prcp(self.data_cfg["basin_ids"])
            .to_array()
            .to_numpy()
            .T
        )

    def inverse_transform(self, target_values):
        """
        Denormalization for output variables

        Parameters
        ----------
        target_values
            output variables

        Returns
        -------
        np.array
            denormalized predictions
        """
        stat_dict = self.stat_dict
        target_cols = self.data_cfg["target_cols"]
        if self.pbm_norm:
            # for pbm's output, its unit is mm/day, so we don't need to recover its unit
            pred = target_values
        else:
            pred = _trans_norm(
                target_values,
                target_cols,
                stat_dict,
                log_norm_cols=self.log_norm_cols,
                to_norm=False,
            )
            for i in range(len(self.data_cfg["target_cols"])):
                var = self.data_cfg["target_cols"][i]
                pred.loc[dict(variable=var)] = _prcp_norm(
                    pred.sel(variable=var).to_numpy(),
                    self.mean_prcp,
                    to_norm=False,
                )
        # add attrs for units
        pred.attrs.update(self.data_target.attrs)
        return pred.to_dataset(dim="variable")

    def get_data_ts(self, to_norm=True) -> np.array:
        """
        Get dynamic input data

        Parameters
        ----------
        rm_nan
            if true, fill NaN value with 0
        to_norm
            if true, perform normalization

        Returns
        -------
        np.array
            the dynamic inputs for modeling
        """
        stat_dict = self.stat_dict
        var_lst = self.data_cfg["relevant_cols"]
        data = self.data_forcing
        data = _trans_norm(
            data, var_lst, stat_dict, log_norm_cols=self.log_norm_cols, to_norm=to_norm
        )
        return data

    def get_data_const(self, to_norm=True) -> np.array:
        """
        Attr data and normalization

        Parameters
        ----------
        rm_nan
            if true, fill NaN value with 0
        to_norm
            if true, perform normalization

        Returns
        -------
        np.array
            the static inputs for modeling
        """
        stat_dict = self.stat_dict
        var_lst = self.data_cfg["constant_cols"]
        data = self.data_attr
        data = _trans_norm(data, var_lst, stat_dict, to_norm=to_norm)
        return data

    def load_data(self):
        """
        Read data and perform normalization for DL models

        Returns
        -------
        tuple
            x: 3-d  gages_num*time_num*var_num
            c: 2-d  gages_num*var_num
        """
        x = self.get_data_ts()
        c = self.get_data_const()
        return x, c
