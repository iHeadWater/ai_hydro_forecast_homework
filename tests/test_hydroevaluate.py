"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2025-06-19 16:20:48
LastEditors: Wenyu Ouyang
Description: Test cases for EvalDeepHydro
FilePath: \hydroevaluate\tests\test_hydroevaluate.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import os

import numpy as np
import pandas as pd
import xarray as xr
from hydroevaluate.hydroevaluate import EvalDeepHydro, EvalHydroModel
from hydroevaluate.configs.config import (
    DEFAULT_cfgs,
    default_config_file,
    update_cfg,
    cmd,
)


def test_load_config():
    eval_deep_hydro = EvalDeepHydro()
    assert "data_cfgs" in eval_deep_hydro.cfgs
    assert "model_cfgs" in eval_deep_hydro.cfgs
    assert "evaluation_cfgs" in eval_deep_hydro.cfgs


def test_model_infer_with_cmd():
    cfg_file = default_config_file()
    # gage_ids = pd.read_csv("data/basin_id(819).csv", dtype={"id": str})[
    #     "id"
    # ].values.tolist()
    args = cmd(
        data_dir=r"C:\data\data_817",
        object_ids=[
            "songliao_21401550",
            "songliao_21401050",
            "camels_01013500",
            "camels_01022500",
        ],
        t_range_test=[("2021-06-01-01", "2021-11-01-01")],
        download=True,
        # pth_path="/home/xushuolong1/hydro/hydroevaluate/data/model_v101/best_model.pth",
        # stat_dict_file="/home/xushuolong1/hydro/hydroevaluate/data/model_v101/dapengscaler_stat.json",
        case_dir=r"C:\Programming\hydro\hydroevaluate\data\model",
        model_type="torchhydro",
        device=[-1],
        model_name="Seq2Seq",
        forecast_length=8,
        rolling=8,
        hindcast_length=240,
        min_time_interval=3,
        min_time_unit="h",
        relevant_cols=["total_precipitation_hourly", "sm_surface"],
        feature_mapping={
            "total_precipitation_hourly": {
                "category": "precipitation",
                "time_ranges": [(0, 248)],
                "offset": 1,
            },
            # "precipitationCal": {
            #     "category": "precipitation",
            #     "time_ranges": [(240, 296)],
            #     "offset": 1,
            # },
            "sm_surface": {
                "category": "soil_moisture",
                "time_ranges": [(0, 248)],
                "offset": 0,
            },
        },
        model_hyperparam={
            "en_input_size": 17,
            "de_input_size": 18,
            "output_size": 2,
            "hidden_size": 256,
            "forecast_length": 8,
            "hindcast_output_window": 1,
            "teacher_forcing_ratio": 0.5,
        },
        revision="v1.0.1",
        api="",
    )
    update_cfg(cfg_file, args)
    eval_deep_hydro = EvalDeepHydro(cfg_file)
    pred = eval_deep_hydro.model_infer()
    print(pred)
    pred.to_netcdf(r"C:\Programming\hydro\hydroevaluate\result\test_21\test.nc")


def test_model_infer():
    # TODO: put this if-else in an update-config function
    # sourcery skip: no-conditionals-in-tests
    if DEFAULT_cfgs["model_cfgs"]["download"]:
        DEFAULT_cfgs["model_cfgs"]["pth_path"] = os.path.join(
            DEFAULT_cfgs["data_cfgs"]["case_dir"],
            "best_model.pth",
        )
        DEFAULT_cfgs["data_cfgs"]["stat_dict_file"] = os.path.join(
            DEFAULT_cfgs["data_cfgs"]["case_dir"],
            "dapengscaler_stat.json",
        )
    eval_deep_hydro = EvalDeepHydro(DEFAULT_cfgs)
    pred = eval_deep_hydro.model_infer()
    print(pred)


class MockDataSource():
    """
    Custom implementation of SelfMadeDataSource that provides fake data with required attributes.
    """

    def __init__(self):
        super().__init__()
        # some functions should be related to data_cfgs, here is just an example

    def generate_time(self, time_unit):
        """
        Generate a time range based on the provided time interval (e.g., '3h', '1h').

        Args:
            time_unit (str): Time interval string (e.g., '3h').

        Returns:
            pd.DatetimeIndex: Generated time range.
        """
        start_time = pd.Timestamp("2015-06-01 01:00:00")
        end_time = pd.Timestamp("2015-10-01 04:00:00")
        return pd.date_range(start=start_time, end=end_time, freq=time_unit)

    def read_ts_xrdataset(self, gage_id_lst, t_range, var_lst, time_units):
        if time_units is None:
            time_units = ["3h"]
        basin = ["songliao_21401050", "songliao_21401550"]
        datasets_by_time_unit = {}

        for unit in time_units:
            time = self.generate_time(unit)
            # Creating fake data for each variable
            total_precipitation_hourly = np.random.rand(len(basin), len(time))

            ds = xr.Dataset(
                {
                    "total_precipitation_hourly": (
                        ("basin", "time"),
                        total_precipitation_hourly,
                    ),
                },
                coords={"basin": basin, "time": time},
            )

            datasets_by_time_unit[unit] = ds

        return datasets_by_time_unit

    def read_attr_xrdataset(self, gage_id_lst, var_lst):
        basin = ["songliao_21401050", "songliao_21401550"]

        # Creating fake data for attributes
        area = np.random.rand(len(basin)) * 1000
        ele_mt_smn = np.random.rand(len(basin)) * 500
        slp_dg_sav = np.random.rand(len(basin)) * 45
        sgr_dk_sav = np.random.rand(len(basin)) * 10
        for_pc_sse = np.random.rand(len(basin)) * 100
        glc_cl_smj = np.random.randint(1, 10, size=len(basin))
        run_mm_syr = np.random.rand(len(basin)) * 1000
        inu_pc_slt = np.random.rand(len(basin)) * 100
        cmi_ix_syr = np.random.rand(len(basin)) * 10
        aet_mm_syr = np.random.rand(len(basin)) * 2000
        snw_pc_syr = np.random.rand(len(basin)) * 100
        swc_pc_syr = np.random.rand(len(basin)) * 100
        gwt_cm_sav = np.random.rand(len(basin)) * 200
        cly_pc_sav = np.random.rand(len(basin)) * 100
        dor_pc_pva = np.random.randint(1, 10, size=len(basin))

        return xr.Dataset(
            {
                "area": (("basin"), area),
                "ele_mt_smn": (("basin"), ele_mt_smn),
                "slp_dg_sav": (("basin"), slp_dg_sav),
                "sgr_dk_sav": (("basin"), sgr_dk_sav),
                "for_pc_sse": (("basin"), for_pc_sse),
                "glc_cl_smj": (("basin"), glc_cl_smj),
                "run_mm_syr": (("basin"), run_mm_syr),
                "inu_pc_slt": (("basin"), inu_pc_slt),
                "cmi_ix_syr": (("basin"), cmi_ix_syr),
                "aet_mm_syr": (("basin"), aet_mm_syr),
                "snw_pc_syr": (("basin"), snw_pc_syr),
                "swc_pc_syr": (("basin"), swc_pc_syr),
                "gwt_cm_sav": (("basin"), gwt_cm_sav),
                "cly_pc_sav": (("basin"), cly_pc_sav),
                "dor_pc_pva": (("basin"), dor_pc_pva),
            },
            coords={"basin": basin},
        )

    def read_mean_prcp(self, gage_id_lst, unit):
        basin = ["songliao_21401050", "songliao_21401550"]
        # Creating fake data for mean precipitation
        pre_mm_syr = np.random.rand(len(basin)) * 2000

        return xr.Dataset(
            {"pre_mm_syr": (("basin"), pre_mm_syr)}, coords={"basin": basin}
        )


def test_model_infer_with_self_made_data():
    data_source = MockDataSource()
    cfg_file = default_config_file()
    args = cmd(
        hindcast_length=240,
        forecast_length=56,
        object_ids=["songliao_21401050", "songliao_21401550"],
        t_range_test=[("2015-06-01-01", "2015-10-01-04")],
        download=False,
        pth_path="/home/xushuolong1/hydro/hydroevaluate/data/train_with_camels_3h_era5land_stlflow/best_model.pth",
        stat_dict_file="/home/xushuolong1/hydro/hydroevaluate/data/train_with_camels_3h_era5land_stlflow/dapengscaler_stat.json",
        model_type="torchhydro",
        model_name="Seq2Seq",
        relevant_cols=["total_precipitation_hourly"],
        target_cols=["streamflow"],
        feature_mapping={
            "total_precipitation_hourly": {
                "category": "precipitation",
                "time_ranges": [(0, 296)],
                "offset": 1,
            },
        },
        model_hyperparam={
            "en_input_size": 16,
            "de_input_size": 17,
            "output_size": 1,
            "hidden_size": 256,
            "forecast_length": 56,
            "hindcast_output_window": 1,
            "teacher_forcing_ratio": 0.5,
        },
    )
    update_cfg(cfg_file, args)
    eval_deep_hydro = EvalDeepHydro(cfg_file, data_source)
    pred = eval_deep_hydro.model_infer()
    print(pred)


def test_hydromodel_infer():
    args = cmd(
        model_type="hydromodel",
        object_ids=["songliao_21401550", "songliao_21401050"],
        relevant_cols=[
            "total_precipitation_hourly",
            "hourly_precipitation",
            "sm_surface",
            "streamflow",
        ],
        t_range_test=[("2016-06-03-01", "2023-11-03-04")],
        feature_mapping={
            "total_precipitation_hourly": {
                "category": "precipitation",
                "time_ranges": [(0, 240)],
                "offset": 1,
            },
            "hourly_precipitation": {
                "category": "precipitation",
                "time_ranges": [(240, 248)],
                "offset": 1,
            },
            "sm_surface": {
                "category": "soil_moisture",
                "time_ranges": [(0, 248)],
                "offset": 0,
            },
        },
    )
    cfg_file = default_config_file()
    update_cfg(cfg_file, args)
    eval_hydro_model = EvalHydroModel(cfg_file)
    eval_hydro_model.model_infer()
