import warnings
from hydroevaluate.dataloader.common import GPM, GFS, SMAP
import yaml
from hydroevaluate.utils.heutils import gee_gpm_to_1h_data, calculate_nse, plot_time_series, gee_gfs_tp_data_process
from hydroevaluate.modelloader.model import load_hydromodel, load_torchmodel
import os

class Evaluator:
    def __init__(self, config):
        self.data_dir = config["data_dir"]
        self.basin_ids = config["basin_ids"]
        self.data_names = config["data_names"]
        self.data_units = config["data_units"]
        self.data_reader = config["data_reader"]
        self.model_type = config["model_type"] # hydromodel or torchhydro
        
    def load_model(self, **kwargs):
        