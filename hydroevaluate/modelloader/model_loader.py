"""
Author: silencesoup silencesoup@outlook.com
Date: 2024-09-03 17:28:41
LastEditors: silencesoup silencesoup@outlook.com
LastEditTime: 2024-09-03 17:31:01
FilePath: /hydroevaluate/hydroevaluate/modelloader/model_loader.py
Description:
"""

from hydroevaluate.modelloader.model_dict import modelloader_dict, modelinfer_dict


class ModelLoader:
    def __init__(self, model_cfg):
        self.model_cfg = model_cfg

    def load_model(self):
        if self.model_cfg["model_type"] in modelloader_dict:
            return modelloader_dict[self.model_cfg["model_type"]](self.model_cfg)
        else:
            raise ValueError(
                f'model type {self.model_cfg["model_type"]} is not supported'
            )

    def infer(self, **kwargs):
        return modelinfer_dict[self.model_cfg["model_type"]](**kwargs)
