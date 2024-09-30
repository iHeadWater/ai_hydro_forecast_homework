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
from torch.utils.data import DataLoader
import numpy as np
import torch
import yaml
from scipy import signal
from yaml import Loader, Dumper
from modelscope import HubApi
from modelscope import snapshot_download
from hydroevaluate.dataloader.data_sets import Seq2SeqDatasetForEval
from torchhydro.trainers.train_utils import (
    calculate_and_record_metrics,
)

from hydroevaluate import SETTING
from hydroevaluate.modelloader.model_loader import ModelLoader
from hydroevaluate.configs.config import DEFAULT_cfgs
from torchhydro.models.model_utils import get_the_device


class HydroEvaluate(ABC):
    def __init__(self, conf_file=None):
        self.conf_dir = SETTING["conf_dir"]
        self.conf_name = conf_file
        self.cfgs = self._load_cfgs()
        self._check_cfgs()

    def _load_cfgs(self):
        # TODO: add more ways to load cfgs
        return DEFAULT_cfgs

    def _check_cfgs(self):
        # TODO: simply check now, more detailed check will be added later
        if "data_cfgs" not in self.cfgs:
            raise KeyError("data_cfgs not found in cfgs file")
        if "model_cfgs" not in self.cfgs:
            raise KeyError("model_cfgs not found in cfgs file")
        if "evaluation_cfgs" not in self.cfgs:
            raise KeyError("evaluation_cfgs not found in cfgs file")

    @abstractmethod
    def _load_model(self):
        pass

    @abstractmethod
    def model_infer(self):
        pass

    @abstractmethod
    def model_evaluate(self):
        pass


class EvalDeepHydro(HydroEvaluate):
    def __init__(self, conf_file=None, data_source=None):
        super().__init__(conf_file)
        if self.cfgs["model_cfgs"]["download"]:
            self._download_model()
        self.modelloader = ModelLoader(self.cfgs["model_cfgs"])
        self.data_set = Seq2SeqDatasetForEval(self.cfgs["data_cfgs"], data_source)
        self.dataloader = DataLoader(
            self.data_set,
            batch_size=int(self.data_set.num_samples / self.n_grid),
            shuffle=False,
            drop_last=False,
            timeout=0,
        )
        self.device_num = self.cfgs["model_cfgs"]["device"]
        self.device = get_the_device(self.device_num)

    @property
    def n_grid(self):
        return len(self.cfgs["data_cfgs"]["object_ids"])

    def _download_model(self):
        api = HubApi()
        api.login(self.cfgs["model_cfgs"]["api"])
        snapshot_download(
            model_id=self.cfgs["model_cfgs"]["model_repo"],
            revision=self.cfgs["model_cfgs"]["revision"],
            local_dir=self.cfgs["model_cfgs"]["local_dir"],
        )

    def _load_model(self):
        return self.modelloader.load_model()

    def model_infer(self):
        eval_cfgs = self.cfgs["evaluation_cfgs"]
        data_cfgs = self.cfgs["data_cfgs"]
        model = self._load_model()
        seq_first = eval_cfgs["seq_first"]
        preds = []
        with torch.no_grad():
            for xs in self.dataloader:
                pred_single = self.modelloader.infer(
                    seq_first=seq_first, model=model, xs=xs
                )
                pred_single = pred_single.cpu().numpy()
                preds.append(torch.tensor(pred_single))
            pred_final = torch.cat(preds, dim=0)
        pred = pred_final.detach().cpu().numpy()
        ngrid = self.n_grid
        if not eval_cfgs["long_seq_pred"]:
            target_len = len(data_cfgs["target_cols"])
            prec_window = data_cfgs["prec_window"]
            batch_size = self.dataloader.batch_size
            if eval_cfgs["rolling"]:
                forecast_length = data_cfgs["horizon"]
                pred = pred[:, prec_window:, :].reshape(
                    ngrid, batch_size, forecast_length, target_len
                )

                pred = pred[:, ::forecast_length, :, :]
                pred = np.concatenate(pred, axis=0).reshape(ngrid, -1, target_len)
                pred = pred[:, :batch_size, :]
            else:
                pred = pred[:, prec_window, :].reshape(ngrid, batch_size, target_len)
        pred = self.data_set.denormalize(pred)
        return pred

    def model_evaluate(self, obs_xr):
        eval_cfgs = self.cfgs["evaluation_cfgs"]
        pred_xr = self.run_model()
        fill_nan = eval_cfgs["fill_nan"]
        eval_log = {}
        for i, col in enumerate(eval_cfgs["target_cols"]):
            obs = obs_xr[col].to_numpy()
            pred = pred_xr[col].to_numpy()
            eval_log = calculate_and_record_metrics(
                obs,
                pred,
                eval_cfgs["metrics"],
                col,
                fill_nan[i] if isinstance(fill_nan, list) else fill_nan,
                eval_log,
            )
        test_log = f" Best Metric {eval_log}"
        print(test_log)
        return eval_log, pred_xr, obs_xr

    def send_report(self, eval_log):
        private_yml = self.cfgs
        # https://zhuanlan.zhihu.com/p/631317974
        send_address = private_yml["email"]["send_address"]
        password = private_yml["email"]["authenticate_code"]
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        login_result = server.login(send_address, password)
        if login_result == (235, b"Authentication successful"):
            self._extracted_from_send_report(
                eval_log, send_address, private_yml, server
            )
        else:
            print("发送失败")

    # TODO Rename this here and in `send_report`
    def _extracted_from_send_report(self, eval_log, send_address, private_yml, server):
        content = yaml.dump(data=eval_log, Dumper=Dumper)
        # https://service.mail.qq.com/detail/124/995
        # https://stackoverflow.com/questions/58223773/send-a-list-of-dictionaries-formatted-with-indents-as-a-string-through-email-u
        msg = MIMEMultipart()
        msg["From"] = f"nickname<{send_address}>"
        msg["To"] = str(
            [f"nickname<{addr}>;" for addr in private_yml["email"]["to_address"]]
        )
        msg["Subject"] = "model_report"
        msg.attach(MIMEText(content, "plain"))
        server.sendmail(
            send_address, private_yml["email"]["to_address"], msg.as_string()
        )
        print("发送成功")
