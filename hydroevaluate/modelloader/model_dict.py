"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 15:09:45
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-03 17:56:05
FilePath: /hydroevaluate/hydroevaluate/modelloader/model_dict.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
"""

from hydroevaluate.modelloader.model import (
    load_hydromodel,
    load_torchmodel,
    infer_hydromodel,
    infer_torchmodel,
)


modelloader_dict = {"hydromodel": load_hydromodel, "torchhydro": load_torchmodel}

modelinfer_dict = {"hydromodel": infer_hydromodel, "torchhydro": infer_torchmodel}
