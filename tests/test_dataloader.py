'''
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 09:50:27
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-03 09:53:28
FilePath: /hydroevaluate/tests/test_dataloader.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from hydroevaluate.dataloader.data_reader import read_training_data

def test_read_training_data():
    # Test with default parameters
    data = read_training_data(
        data_dir='/ftproot/basins-interim',
        basin_ids=["songliao_21401050", "songliao_21401550"],
        vars=["precipitationCal","streamflow"],
        time_range=("2022-01-01", "2022-01-31"),
        time_unit=["1D"],
    )
    print(data)