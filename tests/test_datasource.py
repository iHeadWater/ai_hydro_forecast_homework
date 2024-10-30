"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-10-30 14:03:48
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-10-30 14:04:21
FilePath: /hydroevaluate/tests/test_datasource.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

from hydroevaluate.dataloader.data_source import StandardDataSourceForHydroModel

from hydroevaluate.configs.config import default_config_file


def test_hydromodel_datasource():
    cfg = default_config_file()
    data_source = StandardDataSourceForHydroModel(cfg["data_cfgs"])
    data = data_source.get_p_and_e_dict(["songliao_21401550"])
    print(data)
