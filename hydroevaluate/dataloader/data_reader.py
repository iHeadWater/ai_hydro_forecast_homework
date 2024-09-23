"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 09:49:24
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-03 15:23:59
FilePath: /hydroevaluate/hydroevaluate/dataloader/data_reader.py
Description:
"""

import pandas as pd
import os
import xarray as xr

from hydrodatasource.utils.utils import calculate_basin_offsets
from hydrodatasource.reader.data_source import SelfMadeHydroDataset


class SelfMadeHydroDatasetForEval(SelfMadeHydroDataset):
    def __init__(self, data_path, download=False, time_unit=None):
        super(SelfMadeHydroDataset, self).__init__(data_path, download, time_unit)

    def get_name(self):
        return "SelfMadeHydroDatasetForEval"
