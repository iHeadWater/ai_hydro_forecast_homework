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
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from torch.utils.data import DataLoader
import numpy as np
import torch
import yaml
from scipy import signal
from functools import reduce
from yaml import Loader, Dumper
from modelscope import HubApi
from modelscope import snapshot_download
from hydroevaluate.dataloader.dataloader_dict import dataset_dict
from hydroevaluate.dataloader.data_source import StandardDataSourceForHydroModel
from torchhydro.trainers.train_utils import (
    calculate_and_record_metrics,
)

from hydroevaluate import SETTING
from hydroevaluate.modelloader.model_loader import ModelLoader
from hydroevaluate.configs.config import DEFAULT_cfgs
from torchhydro.models.model_utils import get_the_device


class HydroEvaluate(ABC):
    def __init__(self, conf_file=None):
        self.cfgs = conf_file
        self._check_cfgs()
        output_folder = self.cfgs["evaluation_cfgs"]["output_folder"]
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_file = os.path.join(output_folder, "cfgs.json")
        with open(output_file, "w") as json_file:
            json.dump(self.cfgs, json_file, indent=4)

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
        self.data_source = data_source
        self.data_set = dataset_dict[self.cfgs["data_cfgs"]["dataset"]](
            self.cfgs["data_cfgs"], self.data_source
        )
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
        test_preds = []
        with torch.no_grad():
            for xs in self.dataloader:
                pred = self.modelloader.infer(seq_first=seq_first, model=model, xs=xs)
                test_preds.append(pred.cpu().numpy())
            pred = reduce(lambda x, y: np.vstack((x, y)), test_preds)
        ngrid = self.n_grid
        if eval_cfgs["rolling"]:
            # TODO: now we only guarantee each time has only one value,
            # so we directly reshape the data rather than a real rolling
            nt = self.data_set.nt
            target_len = len(data_cfgs["target_cols"])
            prec_window = data_cfgs["prec_window"]
            forecast_length = data_cfgs["horizon"]
            window_size = prec_window + forecast_length
            rho = data_cfgs["rho"]
            recover_len = nt - rho + prec_window
            samples = int(pred.shape[0] / ngrid)
            pred_ = np.full((ngrid, recover_len, target_len), np.nan)
            # recover pred to pred_ and obs to obs_
            pred_4d = pred.reshape(ngrid, samples, window_size, target_len)
            for i in range(ngrid):
                for j in range(recover_len - window_size + 1):
                    pred_[i, j : j + window_size, :] = pred_4d[i, j, :, :]
            pred = pred_.reshape(ngrid, recover_len, target_len)
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


class EvalHydroModel(HydroEvaluate):
    def __init__(self, cfgs):
        super().__init__(cfgs)
        self.data_cfgs = cfgs["data_cfgs"]
        self.model_cfgs = cfgs["model_cfgs"]
        self.modelloader = ModelLoader(cfgs["model_cfgs"])
        self.data_source = StandardDataSourceForHydroModel(cfgs["data_cfgs"])

    def _load_model(self, gage_id):
        return self.modelloader.load_model(gage_id=gage_id)

    def model_evaluate(self):
        pass

    def model_infer(self):
        gage_id_list = self.cfgs["data_cfgs"]["object_ids"]
        p_and_e_dict = self.data_source.get_p_and_e_dict(gage_id_list)
        for gage_id in gage_id_list:
            try:
                model = self._load_model(gage_id)
                p_and_e_list = p_and_e_dict[gage_id]
                result_list = []
                for p_and_e in p_and_e_list:
                    time_df = p_and_e["time"]
                    p_and_e["rain"] = p_and_e["rain"].fillna(0)
                    p_and_e = p_and_e[["rain", "pet"]].values.reshape(-1, 1, 2)
                    result = self.modelloader.infer(p_and_e=p_and_e, model=model)
                    flattened_array = result.flatten()
                    df_qsim = pd.DataFrame(flattened_array, columns=["qsim"])
                    gage_id_df = pd.DataFrame(
                        [gage_id] * len(df_qsim), columns=["basin"]
                    )
                    df_qsim = pd.concat([gage_id_df, time_df, df_qsim], axis=1)
                    df_qsim = df_qsim[["basin", "time", "qsim"]]
                    df_qsim.columns = ["basin", "time", "flow"]
                    rho = self.data_cfgs["rho"]
                    result = df_qsim.iloc[rho:].reset_index(drop=True)
                    result_list.append(result)
                gage_result = (
                    pd.concat(result_list).sort_values(by="time").reset_index(drop=True)
                )
                if not os.path.exists(self.cfgs["evaluation_cfgs"]["output_folder"]):
                    os.makedirs(self.cfgs["evaluation_cfgs"]["output_folder"])
                gage_result.to_csv(
                    os.path.join(
                        self.cfgs["evaluation_cfgs"]["output_folder"],
                        f"{gage_id}.csv",
                    ),
                    index=False,
                )
            except Exception as e:
                print(e)
