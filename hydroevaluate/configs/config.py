"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 10:16:32
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-04 11:01:45
FilePath: /hydroevaluate/hydroevaluate/cfgss/cfgs.py
Description:
"""

import argparse
import json
import os

SSM_SMAP_NAME = "ssm"
ET_MODIS_NAME = "ET"
Q_CAMELS_US_NAME = "streamflow"
Q_CAMELS_CC_NAME = "Q"
PRCP_DAYMET_NAME = "prcp"
PRCP_NLDAS_NAME = "total_precipitation"
PET_MODIS_NAME = "PET"
PET_NLDAS_NAME = "potential_evaporation"
NLDAS_NAME = "nldas"
ERA5LAND_NAME = "era5land"
ET_ERA5LAND_NAME = "total_evaporation"
PRCP_ERA5LAND_NAME = "total_precipitation"
PET_DAYMET_NAME = "PET"
PET_ERA5LAND_NAME = "potential_evaporation"
DATE_FORMATS = ["%Y-%m-%d-%H", "%Y-%m-%d"]

DEFAULT_cfgs = {
    "data_cfgs": {
        "data_dir": "/ftproot/basins-interim",  # 数据位置，以HydroDataCompiler的处理结果为准
        "json_folder": "/home/xushuolong1/hydro/hydroevaluate/data/json",
        "stat_file_path": "",
        # "object_ids": ["camels_01013500", "camels_01030500"],
        "object_ids": ["songliao_21401550", "songliao_21401050"],
        "min_time_unit": "h",
        "min_time_interval": 3,
        "t_range_test": [("2019-06-01-01", "2019-10-01-01")],
        "var_lst": [
            "total_precipitation_hourly",
            # "precipitationCal",
            # "hourly_precipitation",
            # "streamflow",
            "sm_surface",
            # "sm_rootzone",
        ],
        "var_self_orgnized": True,
        "feature_mapping": {
            "total_precipitation_hourly": {
                "category": "precipitation",
                "time_ranges": [(0, 296)],
                "offset": 1,
            },
            # "precipitationCal": {
            #     "category": "precipitation",
            #     "time_ranges": [(0, 248)],
            #     "offset": 1,
            # },
            # "hourly_precipitation": {
            #     "category": "precipitation",
            #     "time_ranges": [(0, 248)],
            #     "offset": 0,
            # },
            "sm_surface": {
                "category": "soil_moisture",
                "time_ranges": [(0, 296)],
                "offset": 0,
            },
            # "sm_rootzone": {
            #     "category": "soil_moisture",
            #     "time_ranges": [(3, 8)],
            #     "offset": 0,
            # },
        },
        "features_only_rho": ["soil_moisture"],
        "target_cols": ["streamflow", "sm_surface"],
        "rho": 240,
        "horizon": 56,
        "warmup_length": 0,
        "prec_window": 1,
        "constant_vars": [
            "area",  # 面积
            "ele_mt_smn",  # 海拔(空间平均)
            "slp_dg_sav",  # 地形坡度 (空间平均)
            "sgr_dk_sav",  # 河流坡度 (平均)
            "for_pc_sse",  # 森林覆盖率
            "glc_cl_smj",  # 土地覆盖类型
            "run_mm_syr",  # 陆面径流 (流域径流的空间平均值)
            "inu_pc_slt",  # 淹没范围 (长期最大)
            "cmi_ix_syr",  # 气候湿度指数
            "aet_mm_syr",  # 实际蒸散发 (年平均)
            "snw_pc_syr",  # 雪盖范围 (年平均)
            "swc_pc_syr",  # 土壤水含量
            "gwt_cm_sav",  # 地下水位深度
            "cly_pc_sav",  # 土壤中的黏土、粉砂、砂粒含量
            "dor_pc_pva",  # 调节程度
        ],
        "relevant_rm_nan": True,
        "constant_rm_nan": True,
        "scaler_params": {
            "prcp_norm_cols": [
                Q_CAMELS_US_NAME,
                "streamflow",
                Q_CAMELS_CC_NAME,
                "qobs",
                "qobs_mm_per_hour",
            ],
            "gamma_norm_cols": [
                PRCP_DAYMET_NAME,
                "pr",
                # PRCP_ERA5LAND_NAME is same as PRCP_NLDAS_NAME
                PRCP_NLDAS_NAME,
                "pre",
                # pet may be negative, but we set negative as 0 because of gamma_norm_cols
                # https://earthscience.stackexchange.com/questions/12031/does-negative-reference-evapotranspiration-make-sense-using-fao-penman-monteith
                "pet",
                # PET_ERA5LAND_NAME is same as PET_NLDAS_NAME
                PET_NLDAS_NAME,
                ET_MODIS_NAME,
                "LE",
                PET_MODIS_NAME,
                "PLE",
                "GPP",
                "Ec",
                "Es",
                "Ei",
                "ET_water",
                "ET_sum",
                SSM_SMAP_NAME,
                "susm",
                "smp",
                "ssma",
                "susma",
            ],
            "pbm_norm": False,
        },
    },
    "model_cfgs": {
        "json_folder": "/home/xushuolong1/hydro/hydroevaluate/data/json",
        "yaml_folder": "/home/xushuolong1/hydro/hydroevaluate/data/yaml",
        "download": True,
        "model_repo": "iHeadWater/torchhydro-seq2seq-lstm",
        "api": "",
        "revision": "v1.0.1",
        "local_dir": "",
        "model_type": "torchhydro",
        "model_name": "Seq2Seq",
        "model_hyperparam": {
            "en_input_size": 17,
            "de_input_size": 18,
            "output_size": 2,
            "hidden_size": 256,
            "forecast_length": 56,
            "prec_window": 1,
            "teacher_forcing_ratio": 0.5,
        },
        "pth_path": "",
        "area": 1000,
        "target_unit": "m^3/s",
        "device": [0],
    },
    "evaluation_cfgs": {
        "output_folder": "/home/xushuolong1/hydro/hydroevaluate/data/output",
        "seq_first": False,
        "rolling": True,
        "long_seq_pred": False,
    },
}


def default_config_file():
    """
    Default config file for all models/data/training parameters in this repo.

    Returns
    -------
    dict
        configurations
    """
    return DEFAULT_cfgs


def cmd(
    data_dir=None,
    json_folder=None,
    stat_file_path=None,
    object_ids=None,
    min_time_unit=None,
    min_time_interval=None,
    t_range_test=None,
    var_lst=None,
    var_self_orgnized=None,
    feature_mapping=None,
    features_only_rho=None,
    target_cols=None,
    rho=None,
    horizon=None,
    warmup_length=None,
    prec_window=None,
    constant_vars=None,
    relevant_rm_nan=None,
    constant_rm_nan=None,
    scaler_params=None,
    yaml_folder=None,
    download=None,
    model_repo=None,
    api=None,
    revision=None,
    local_dir=None,
    model_type=None,
    model_name=None,
    model_hyperparam=None,
    pth_path=None,
    p_and_e=None,
    area=None,
    calibrated_norm_param_file=None,
    param_range_file=None,
    model_info_file=None,
    target_unit=None,
    device=None,
    seq_first=None,
    rolling=None,
    long_seq_pred=None,
    output_folder=None,
):
    """Command-line argument parser for updating configuration."""
    parser = argparse.ArgumentParser(description="Update model/data configuration.")

    # Add arguments for key configurations (只添加关键参数，其他的可以根据需要扩展)
    parser.add_argument(
        "--data_dir", type=str, help="Path to the data directory.", default=data_dir
    )
    parser.add_argument(
        "--json_folder", type=str, help="Path to the json folder.", default=json_folder
    )
    parser.add_argument(
        "--stat_file_path",
        type=str,
        help="Path to the stat file.",
        default=stat_file_path,
    )
    parser.add_argument(
        "--object_ids",
        type=list,
        help="Object IDs, ususally basin_ids",
        default=object_ids,
    )
    parser.add_argument(
        "--min_time_unit", type=str, help="Minimum time unit.", default=min_time_unit
    )
    parser.add_argument(
        "--min_time_interval",
        type=int,
        help="Minimum time interval.",
        default=min_time_interval,
    )
    parser.add_argument(
        "--t_range_test", type=list, help="Test time range.", default=t_range_test
    )
    parser.add_argument("--var_lst", type=list, help="Variable list.", default=var_lst)
    parser.add_argument(
        "--var_self_orgnized",
        type=bool,
        help="Variable self orgnized or not.",
        default=var_self_orgnized,
    )
    parser.add_argument(
        "--feature_mapping",
        type=json.loads,
        help="How to self organize the features.",
        default=feature_mapping,
    )
    parser.add_argument(
        "--features_only_rho",
        type=list,
        help="Features only rho.",
        default=features_only_rho,
    )
    parser.add_argument(
        "--target_cols", type=list, help="Target columns.", default=target_cols
    )
    parser.add_argument("--rho", type=int, help="Rho.", default=rho)
    parser.add_argument("--horizon", type=int, help="Horizon.", default=horizon)
    parser.add_argument(
        "--warmup_length", type=int, help="Warmup length.", default=warmup_length
    )
    parser.add_argument(
        "--prec_window", type=int, help="Prec window.", default=prec_window
    )
    parser.add_argument(
        "--constant_vars", type=str, help="Constant vars.", default=constant_vars
    )
    parser.add_argument(
        "--relevant_rm_nan", type=bool, help="Relevant rm nan.", default=relevant_rm_nan
    )
    parser.add_argument(
        "--constant_rm_nan", type=bool, help="Constant rm nan.", default=constant_rm_nan
    )
    parser.add_argument(
        "--scaler_params", type=json.loads, help="Scaler params.", default=scaler_params
    )
    parser.add_argument(
        "--yaml_folder", type=str, help="Yaml folder.", default=yaml_folder
    )
    parser.add_argument(
        "--download",
        type=bool,
        help="Download model from modelscope.",
        default=download,
    )
    parser.add_argument(
        "--model_repo", type=str, help="Model repo.", default=model_repo
    )
    parser.add_argument("--api", type=str, help="API.", default=api)
    parser.add_argument("--revision", type=str, help="Revision.", default=revision)
    parser.add_argument("--local_dir", type=str, help="Local dir.", default=local_dir)
    parser.add_argument(
        "--model_type", type=str, help="Model type.", default=model_type
    )
    parser.add_argument(
        "--model_name", type=str, help="Model name.", default=model_name
    )
    parser.add_argument(
        "--model_hyperparam",
        type=json.loads,
        help="Model hyperparam.",
        default=model_hyperparam,
    )
    parser.add_argument("--pth_path", type=str, help="Pth path.", default=pth_path)
    parser.add_argument("--p_and_e", type=str, help="P and e.", default=p_and_e)
    parser.add_argument("--area", type=float, help="Area.", default=area)
    parser.add_argument(
        "--calibrated_norm_param_file",
        type=str,
        help="Calibrated norm param file.",
        default=calibrated_norm_param_file,
    )
    parser.add_argument(
        "--param_range_file",
        type=str,
        help="Param range file.",
        default=param_range_file,
    )
    parser.add_argument(
        "--model_info_file", type=str, help="Model info file.", default=model_info_file
    )
    parser.add_argument(
        "--target_unit", type=str, help="Target unit.", default=target_unit
    )
    parser.add_argument("--device", type=str, help="Device.", default=device)
    parser.add_argument("--seq_first", type=bool, help="Seq first.", default=seq_first)
    parser.add_argument("--rolling", type=bool, help="Rolling.", default=rolling)
    parser.add_argument(
        "--long_seq_pred", type=bool, help="Long seq pred.", default=long_seq_pred
    )
    parser.add_argument(
        "--output_folder", type=str, help="Xaj Output folder.", default=output_folder
    )

    # Parse command-line arguments
    args, _ = parser.parse_known_args()

    return args


def update_cfg(cfg_file, new_args):
    """
    Update the default configuration based on the provided arguments.

    Parameters
    ----------
    cfg_file : dict
        The original configuration dictionary.
    new_args : argparse.Namespace
        The parsed arguments from command-line input.
    """
    print("Updating configuration file...")

    if new_args.data_dir:
        cfg_file["data_cfgs"]["data_dir"] = new_args.data_dir
    if new_args.json_folder:
        cfg_file["data_cfgs"]["json_folder"] = new_args.json_folder
        cfg_file["model_cfgs"]["json_folder"] = new_args.json_folder
    if new_args.object_ids:
        cfg_file["data_cfgs"]["object_ids"] = new_args.object_ids
    if new_args.min_time_unit:
        cfg_file["data_cfgs"]["min_time_unit"] = new_args.min_time_unit
    if new_args.min_time_interval:
        cfg_file["data_cfgs"]["min_time_interval"] = new_args.min_time_interval
    if new_args.t_range_test:
        cfg_file["data_cfgs"]["t_range_test"] = new_args.t_range_test
    if new_args.var_lst:
        cfg_file["data_cfgs"]["var_lst"] = new_args.var_lst
    if new_args.var_self_orgnized:
        cfg_file["data_cfgs"]["var_self_orgnized"] = new_args.var_self_orgnized
    if new_args.feature_mapping:
        cfg_file["data_cfgs"]["feature_mapping"] = new_args.feature_mapping
    if new_args.features_only_rho:
        cfg_file["data_cfgs"]["features_only_rho"] = new_args.features_only_rho
    if new_args.target_cols:
        cfg_file["data_cfgs"]["target_cols"] = new_args.target_cols
    if new_args.rho:
        cfg_file["data_cfgs"]["rho"] = new_args.rho
    if new_args.horizon:
        cfg_file["data_cfgs"]["horizon"] = new_args.horizon
    if new_args.warmup_length:
        cfg_file["data_cfgs"]["warmup_length"] = new_args.warmup_length
    if new_args.prec_window:
        cfg_file["data_cfgs"]["prec_window"] = new_args.prec_window
    if new_args.constant_vars:
        cfg_file["data_cfgs"]["constant_vars"] = new_args.constant_vars
    if new_args.relevant_rm_nan:
        cfg_file["data_cfgs"]["relevant_rm_nan"] = new_args.relevant_rm_nan
    if new_args.constant_rm_nan:
        cfg_file["data_cfgs"]["constant_rm_nan"] = new_args.constant_rm_nan
    if new_args.scaler_params:
        cfg_file["data_cfgs"]["scaler_params"] = new_args.scaler_params
    if new_args.yaml_folder:
        cfg_file["model_cfgs"]["yaml_folder"] = new_args.yaml_folder
    if new_args.download:
        cfg_file["model_cfgs"]["download"] = new_args.download
        cfg_file["model_cfgs"]["local_dir"] = new_args.local_dir
        cfg_file["model_cfgs"]["pth_path"] = os.path.join(
            cfg_file["model_cfgs"]["local_dir"],
            "best_model.pth",
        )
        cfg_file["data_cfgs"]["stat_file_path"] = os.path.join(
            cfg_file["model_cfgs"]["local_dir"],
            "dapengscaler_stat.json",
        )
    elif new_args.pth_path and new_args.stat_file_path:
        cfg_file["model_cfgs"]["download"] = False
        cfg_file["model_cfgs"]["pth_path"] = new_args.pth_path
        cfg_file["data_cfgs"]["stat_file_path"] = new_args.stat_file_path
    if new_args.model_repo:
        cfg_file["model_cfgs"]["model_repo"] = new_args.model_repo
    if new_args.api:
        cfg_file["model_cfgs"]["api"] = new_args.api
    if new_args.revision:
        cfg_file["model_cfgs"]["revision"] = new_args.revision
    if new_args.model_type:
        cfg_file["model_cfgs"]["model_type"] = new_args.model_type
    if new_args.model_name:
        cfg_file["model_cfgs"]["model_name"] = new_args.model_name
    if new_args.model_hyperparam:
        cfg_file["model_cfgs"]["model_hyperparam"] = new_args.model_hyperparam
    if new_args.p_and_e:
        cfg_file["model_cfgs"]["p_and_e"] = new_args.p_and_e
    if new_args.area:
        cfg_file["model_cfgs"]["area"] = new_args.area
    if new_args.calibrated_norm_param_file:
        cfg_file["model_cfgs"][
            "calibrated_norm_param_file"
        ] = new_args.calibrated_norm_param_file
    if new_args.param_range_file:
        cfg_file["model_cfgs"]["param_range_file"] = new_args.param_range_file
    if new_args.model_info_file:
        cfg_file["model_cfgs"]["model_info_file"] = new_args.model_info_file
    if new_args.target_unit:
        cfg_file["model_cfgs"]["target_unit"] = new_args.target_unit
    if new_args.device:
        cfg_file["model_cfgs"]["device"] = new_args.device
    if new_args.seq_first:
        cfg_file["evaluation_cfgs"]["seq_first"] = new_args.seq_first
    if new_args.rolling:
        cfg_file["evaluation_cfgs"]["rolling"] = new_args.rolling
    if new_args.long_seq_pred:
        cfg_file["evaluation_cfgs"]["long_seq_pred"] = new_args.long_seq_pred
    if new_args.output_folder:
        cfg_file["evaluation_cfgs"]["output_folder"] = new_args.output_folder

    print("Configuration updated successfully.")
