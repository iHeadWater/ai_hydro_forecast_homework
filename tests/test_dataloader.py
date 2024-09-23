"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 09:50:27
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-04 16:10:20
FilePath: /hydroevaluate/tests/test_dataloader.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

import pytest
from hydroevaluate.dataloader.data_processor import DapengScalerForEval
from hydrodatasource.reader.data_source import SelfMadeHydroDataset


@pytest.fixture
def default_config():
    config = {
        "data_cfg": {
            "data_dir": "/ftproot/basins-interim",
            "stat_file_path": "/home/xushuolong1/hydro/hydroevaluate/data/model/dapengscaler_stat.json",
            "object_ids": ["songliao_21401550", "songliao_21401050"],
            "data_unit": ["3h"],
            "var_lst": ["precipitationCal", "streamflow"],
            "t_range_test": ["2018-01-01", "2018-03-31"],
            "constant_vars": [
                "area",
                "ele_mt_smn",
                "slp_dg_sav",
                "sgr_dk_sav",
                "for_pc_sse",
                "glc_cl_smj",
                "run_mm_syr",
                "inu_pc_slt",
                "cmi_ix_syr",
                "aet_mm_syr",
                "snw_pc_syr",
                "swc_pc_syr",
                "gwt_cm_sav",
                "cly_pc_sav",
                "dor_pc_pva",
            ],
        },
        "eval_cfg": {
            "seq_first": True,
        },
    }
    data_source = SelfMadeHydroDataset(config["data_cfg"]["data_dir"])
    scaler = DapengScalerForEval(
        relevant_vars=config["data_cfg"]["var_lst"],
        constant_vars=config["data_cfg"]["constant_vars"],
        data_cfg=config["data_cfg"],
        data_source=data_source,
    )
    return config, scaler


def test_read_mean_prcp(default_config):
    _, scaler = default_config
    mean_prcp = scaler.mean_prcp
    print(mean_prcp)
