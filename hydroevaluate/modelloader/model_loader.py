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
    def __init__(self, model_cfgs):
        self.model_cfgs = model_cfgs

    @property
    def model_type(self):
        return self.model_cfgs["model_type"]

    def load_model(self):
        if self.model_cfgs["model_type"] in modelloader_dict:
            return modelloader_dict[self.model_cfgs["model_type"]](self.model_cfgs)
        else:
            raise ValueError(
                f'model type {self.model_cfgs["model_type"]} is not supported'
            )

    def infer(self, **kwargs):
        return modelinfer_dict[self.model_cfgs["model_type"]](**kwargs)
