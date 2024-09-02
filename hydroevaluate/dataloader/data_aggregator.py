'''
Author: silencesoup silencesoup@outlook.com
Date: 2024-08-29 09:16:19
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-08-30 14:14:22
FilePath: /hydroevaluate/hydroevaluate/dataloader/agg.py
Description: 
'''
import pandas as pd

from hydroevaluate.dataloader.data_reader import read_single_file
from hydroevaluate.utils.heutils import convert_units

def aggregate_dataframe(df, units):
    agg_df = convert_units(df, units)