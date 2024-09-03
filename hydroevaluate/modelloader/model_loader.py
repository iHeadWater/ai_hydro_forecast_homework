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
    def __init__(self, config):
        self.config = config

    def load_model(self):
        if self.config["model_config"]["model_type"] in modelloader_dict:
            return modelloader_dict[self.config["model_config"]["model_type"]](
                self.config
            )
        else:
            raise ValueError(f'model type {self.config["model_type"]} is not supported')

    def infer(self, **kwargs):
        return modelinfer_dict[self.config["model_config"]["model_type"]](**kwargs)
