import warnings
from hydroevaluate.dataloader.common import GPM, GFS, SMAP
import yaml
from hydroevaluate.utils.heutils import (
    gee_gpm_to_1h_data,
    calculate_nse,
    plot_time_series,
    gee_gfs_tp_data_process,
)
from hydroevaluate.modelloader.model import load_hydromodel, load_torchmodel
import os


class Evaluator:
    def __init__(self, cfg):
        self.data_dir = cfg["data_dir"]
        self.basin_ids = cfg["basin_ids"]
        self.data_unit = cfg["data_unit"]
        self.data_reader = cfg["data_reader"]
        self.model_type = cfg["model_type"]  # hydromodel or torchhydro

    def load_model(self, **kwargs):
        pass
