"""
Author: Wenyu Ouyang
Date: 2025-01-11 21:07:20
LastEditTime: 2025-01-11 21:07:43
LastEditors: Wenyu Ouyang
Description: dataloader for model evaluation
FilePath: \hydroevaluate\hydroevaluate\dataloader\dataloader_dict.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

from abc import ABC, abstractmethod


class HydroDataLoader(ABC):
    def __init__(self, conf_file=None):
        """We use a hydrodataloader to load tensor data for model evaluation
        It needs a configuration file to specify the variables and its corresponding parameters, such as the time range
        TODO: We need to implement the dataloader function to load the data

        Parameters
        ----------
        conf_file : _type_, optional
            _description_, by default None
        """
        self.cfgs = conf_file

    @abstractmethod
    def dataloader(self):
        pass
