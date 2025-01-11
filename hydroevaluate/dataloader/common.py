"""
Author: Wenyu Ouyang
Date: 2024-05-31 14:21:54
LastEditTime: 2024-06-03 16:41:04
LastEditors: Wenyu Ouyang
Description: The common class for loading data
FilePath: \hydroevaluate\hydroevaluate\dataloader\common.py
Copyright (c) 2023-2024 Wenyu Ouyang. All rights reserved.
"""

import logging

import numpy as np

logging.getLogger().setLevel(logging.INFO)


def concat_x(x, basin, idx, feature_mapping):
    unique_categories = []
    for config in feature_mapping.values():
        if config["category"] not in unique_categories:
            unique_categories.append(config["category"])
    category_to_index = {
        category: idx for idx, category in enumerate(unique_categories)
    }
    seq_input = x[basin, idx:, :]  # shape: (seq_length, feature)

    # 动态生成时间范围
    time_ranges = []
    for config in feature_mapping.values():
        time_ranges.extend(config["time_ranges"])

    max_time = max(
        end for feature in feature_mapping.values() for _, end in feature["time_ranges"]
    )

    x = np.zeros((max_time, len(category_to_index)))

    for i, (feature, info) in enumerate(feature_mapping.items()):
        category = info["category"]
        time_ranges = info["time_ranges"]
        category_index = category_to_index[category]

        for start, end in time_ranges:
            x[start:end, category_index] += seq_input[start:end, i]
    return x
