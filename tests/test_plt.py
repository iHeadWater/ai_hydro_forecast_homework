"""
Author: 'silencesoup' 'silencesoup@outlook.com'
Date: 2025-01-07 18:16:11
LastEditors: 'silencesoup' 'silencesoup@outlook.com'
LastEditTime: 2025-01-07 18:16:35
FilePath: \hydroevaluate\tests\test_plt.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

from hydroevaluate.evaluator.plt import plt_by_nc


def test_plt_by_nc():
    plt_by_nc(
        pred_nc=r"C:\Programming\hydro\hydroevaluate\result\test_21\test.nc",
        basin_ids=[
            "songliao_21401550",
            "songliao_21401050",
            "camels_01013500",
            "camels_01022500",
        ],
        basin_info_csv=r"C:\Programming\hydro\hydroevaluate\data\basin_info.csv",
        time_unit="3h",
        project_name="test_21",
        time_range=["2021-06-01-01", "2021-11-01-01"],
    )
