"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 10:16:32
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-04 11:01:45
FilePath: /hydroevaluate/hydroevaluate/cfgs/cfg.py
Description:
"""

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

DEFAULT_cfg = {
    "data_cfg": {
        "data_dir": "/ftproot/basins-interim",
        "stat_file_path": "/home/xushuolong1/hydro/hydroevaluate/data/model/dapengscaler_stat.json",
        "basin_ids": ["songliao_21401050", "songliao_21401550"],
        "data_unit": ["3h"],
        "interval": 3,
        "time_range": [["2022-01-01-01", "2022-03-31-01"]],
        "var_lst": ["total_precipitation_hourly", "sm_surface"],
        "output_vars": ["streamflow", "sm_surface"],
        "rho": 240,
        "horizon": 56,
        "warmup_length": 0,
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
    "model_cfg": {
        "model_type": "hydromodel",
        "p_and_e": [],
        "area": 1000,
        "calibrated_norm_param_file": None,
        "param_range_file": None,
        "model_info_file": None,
        "target_unit": "m^3/s",
    },
    "evaluation_cfg": {
        "seq_first": True,
        "rolling": True,
        "long_seq_pred": False,
    },
}
