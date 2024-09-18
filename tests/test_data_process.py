"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 10:41:42
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-18 13:38:10
FilePath: /hydroevaluate/tests/test_data_process.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

from hydroevaluate.dataloader.common import GPM, GFS, SMAP
import pandas as pd


def test_gpm_process():
    start_time = "2024-06-02 00:00:00"
    end_time = "2024-06-04 00:00:00"
    t_range_test = [start_time, end_time]
    gpm = GPM(["gpm_tp"])
    gpm_dataarray = gpm.basin_mean_process("21401550", t_range_test, "gpm_tp")
    print(gpm_dataarray)


def test_gpm_process_without_endtime():
    start_time = "2024-06-01 00:00:00"
    end_time = None
    t_range_test = [start_time, end_time]
    gpm = GPM(["gpm_tp"])
    gpm_dataarray = gpm.basin_mean_process("21401550", t_range_test, "gpm_tp")
    print(gpm_dataarray)


def test_gfs_tp_process():
    start_time = "2024-06-02 00:00:00"
    end_time = "2024-06-04 00:00:00"
    t_range_test = [start_time, end_time]
    gfs = GFS(["gfs_tp"])
    gfs_dataarray = gfs.basin_mean_process("21401550", t_range_test, "gfs_tp")
    print(gfs_dataarray)


def test_gfs_soilw_process():
    start_time = "2024-06-02 00:00:00"
    end_time = "2024-06-04 00:00:00"
    t_range_test = [start_time, end_time]
    gfs = GFS(["gfs_soilw"])
    gfs_dataarray = gfs.basin_mean_process("21401550", t_range_test, "gfs_soilw")
    print(gfs_dataarray)


def test_smap_process():
    start_time = "2024-05-15 00:00:00"
    end_time = "2024-06-04 00:00:00"
    t_range_test = [start_time, end_time]
    smap = SMAP(["smap_sm_surface"])
    smap_dataarray = smap.basin_mean_process(
        "21401550", t_range_test, "smap_sm_surface"
    )
    print(smap_dataarray)
