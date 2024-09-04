"""
Author: Wenyu Ouyang
Date: 2024-05-30 09:11:04
LastEditTime: 2024-06-03 15:20:23
LastEditors: Wenyu Ouyang
Description: main function for hydroevaluate
FilePath: \hydroevaluate\hydroevaluate\hydroevaluate.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

# pytest model_stream.py::test_auto_stream
from abc import ABC, abstractmethod
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import numpy as np
import torch
import yaml
from scipy import signal
from yaml import Loader, Dumper

from torchhydro.trainers.train_utils import (
    calculate_and_record_metrics,
)

from hydroevaluate import SETTING
from hydroevaluate.dataloader.dataloader import DataLoader
from hydroevaluate.modelloader.model_loader import ModelLoader


class HydroEvaluate(ABC):
    def __init__(self, conf_file=None):
        self.conf_dir = SETTING["conf_dir"]
        self.conf_name = conf_file
        self.cfg = self._load_cfg()
        self._check_cfg()

    def _load_cfg(self):
        cfg_name = self.conf_name
        if cfg_name is None:
            # TODO: we chose the first as the default, later we will handle with multiple cfg files
            cfg_name = os.listdir(self.conf_dir)[0]
        with open(os.path.join(self.conf_dir, cfg_name), "r") as fp:
            cfg = yaml.load(fp, Loader)
        return cfg

    def _check_cfg(self):
        # TODO: simply check now, more detailed check will be added later
        if "data_cfg" not in self.cfg:
            raise KeyError("data_cfg not found in cfg file")
        if "model_cfg" not in self.cfg:
            raise KeyError("model_cfg not found in cfg file")
        if "evaluation_cfg" not in self.cfg:
            raise KeyError("evaluation_cfg not found in cfg file")

    @abstractmethod
    def _load_model(self):
        pass

    @abstractmethod
    def _load_data(self):
        pass

    @abstractmethod
    def model_infer(self):
        pass

    @abstractmethod
    def model_evaluate(self):
        pass


class EvalDeepHydro(HydroEvaluate):
    def __init__(self, conf_file=None):
        super().__init__(conf_file)
        self.modelloader = ModelLoader(self.cfg["model_cfg"])
        self.dataloader = DataLoader(self.cfg["data_cfg"])

    def _load_model(self):
        return self.modelloader.load_model()

    def _load_data(self):
        return self.dataloader.load_data()

    def model_infer(self):
        eval_cfg = self.cfg["evaluation_cfg"]
        dataset = self._load_data()
        model = self._load_model()
        seq_first = eval_cfg["seq_first"]
        with torch.no_grad():
            pred = self.modelloader.infer(seq_first, model, dataset)
            pred = pred.cpu().numpy()
        ngrid = dataset.ngrid
        if not eval_cfg["long_seq_pred"]:
            target_len = len(eval_cfg["output_vars"])
            prec_window = eval_cfg["prec_window"]
            if eval_cfg["rolling"]:
                forecast_length = eval_cfg["forecast_length"]
                pred = pred[:, prec_window:, :].reshape(
                    ngrid, batch_size, forecast_length, target_len
                )

                pred = pred[:, ::forecast_length, :, :]
                pred = np.concatenate(pred, axis=0).reshape(ngrid, -1, target_len)
                pred = pred[:, :batch_size, :]
            else:
                pred = pred[:, prec_window, :].reshape(ngrid, batch_size, target_len)
        return dataset.denormalize(pred)

    def model_evaluate(self, obs_xr):
        eval_cfg = self.cfg["evaluation_cfg"]
        pred_xr = self.run_model()
        fill_nan = eval_cfg["fill_nan"]
        eval_log = {}
        for i, col in enumerate(eval_cfg["output_vars"]):
            obs = obs_xr[col].to_numpy()
            pred = pred_xr[col].to_numpy()
            eval_log = calculate_and_record_metrics(
                obs,
                pred,
                eval_cfg["metrics"],
                col,
                fill_nan[i] if isinstance(fill_nan, list) else fill_nan,
                eval_log,
            )
        test_log = f" Best Metric {eval_log}"
        print(test_log)
        return eval_log, pred_xr, obs_xr

    def send_report(self, eval_log):
        private_yml = self.cfg
        # https://zhuanlan.zhihu.com/p/631317974
        send_address = private_yml["email"]["send_address"]
        password = private_yml["email"]["authenticate_code"]
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        login_result = server.login(send_address, password)
        if login_result == (235, b"Authentication successful"):
            content = yaml.dump(data=eval_log, Dumper=Dumper)
            # https://service.mail.qq.com/detail/124/995
            # https://stackoverflow.com/questions/58223773/send-a-list-of-dictionaries-formatted-with-indents-as-a-string-through-email-u
            msg = MIMEMultipart()
            msg["From"] = "nickname<" + send_address + ">"
            msg["To"] = str(
                [
                    "nickname<" + addr + ">;"
                    for addr in private_yml["email"]["to_address"]
                ]
            )
            msg["Subject"] = "model_report"
            msg.attach(MIMEText(content, "plain"))
            server.sendmail(
                send_address, private_yml["email"]["to_address"], msg.as_string()
            )
            print("发送成功")
        else:
            print("发送失败")
