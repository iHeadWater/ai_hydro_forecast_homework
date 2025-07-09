"""
Author: zhuanglaihong
Date: 2025-06-24 16:42:48
LastEditTime: 2025-07-07 11:16:22
LastEditors: zhuanglaihong
Description: Box plot visualization tools for hydrological evaluation and analysis
FilePath: \hydroevaluate\hydroevaluate\evaluator\box_plot.py
Copyright: Copyright (c) 2021-2024 zhuanglaihong. All rights reserved.
""" 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from pathlib import Path
from matplotlib.patches import Patch


class BasinBoxplotTool:
    """流域箱型图绘制工具类，整合了多种箱型图绘制功能"""
    
    def __init__(self):
        # 默认颜色方案
        self.colors = ['#84a8e3', '#e38484', '#99d594', '#fed98e', '#fc8d59']
        self.individual_regional_palette = {"Individual": "lightblue", "Regional": "lightcoral"}
    
    def _ensure_output_dir(self, output_path):
        """确保输出目录存在"""
        if isinstance(output_path, str):
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
        elif output_path is not None:
            if not os.path.exists(output_path):
                os.makedirs(output_path, exist_ok=True)
    
    def _auto_detect_metrics(self, df, exclude_cols=None):
        """自动检测数据框中的指标列"""
        if exclude_cols is None:
            exclude_cols = {"folder", "basin_id", "basin", "method", "data_type", 
                           "comparison_type", "method_name", "loss"}
        
        return [col for col in df.columns if col not in exclude_cols 
                and pd.api.types.is_numeric_dtype(df[col])]
    
    def _load_csv_data(self, csv_path, **kwargs):
        """加载CSV文件数据，处理异常"""
        try:
            df = pd.read_csv(csv_path)
            # 添加额外的列
            for key, value in kwargs.items():
                df[key] = value
            return df
        except FileNotFoundError:
            print(f"错误: 未找到文件 {csv_path}")
        except Exception as e:
            print(f"读取文件 {csv_path} 时出错: {str(e)}")
        return None
    
    def create_boxplot_from_folders(self, folder_paths, output_path, folder_names=None, metric_names=None):
        """从多个文件夹中读取metric_inflow.csv文件，生成每个指定指标的箱型图

        Parameters:
        folder_paths: list, 包含多个文件夹路径的列表
        output_path: str, 输出图片的保存路径
        folder_names: list, 可选，文件夹的显示名称，如果不提供则使用文件夹名
        metric_names: list, 可选，指定要绘制的指标名（如["NSE", "RMSE"]），如果不提供则自动遍历所有数值型指标
        """
        # 确保输出目录存在
        self._ensure_output_dir(output_path)
        
        # 如果没有提供文件夹名称，则使用文件夹路径的最后一部分
        if folder_names is None:
            folder_names = [os.path.basename(path) for path in folder_paths]

        # 读取每个文件夹中的CSV文件
        all_data = []
        for i, folder_path in enumerate(folder_paths):
            csv_path = os.path.join(folder_path, "metric_inflow.csv")
            df = self._load_csv_data(csv_path, folder=folder_names[i])
            if df is not None:
                all_data.append(df)
                print(f"成功读取 {csv_path}: {len(df)} 条记录")

        # 合并所有数据
        if not all_data:
            print("错误: 没有成功读取任何数据")
            return None

        combined_df = pd.concat(all_data, ignore_index=True)

        # 自动检测指标名（如果未指定）
        if metric_names is None:
            metric_names = self._auto_detect_metrics(combined_df)

        if not metric_names:
            print("错误: 没有可用的指标名")
            return None

        # 针对每个指标绘制箱型图
        for metric in metric_names:
            if metric not in combined_df.columns:
                print(f"警告: 未找到指标 {metric}，跳过")
                continue

            # 只保留当前指标和文件夹标识
            df_subset = combined_df[["folder", metric]].copy()
            df_subset = df_subset.dropna(subset=[metric])

            if df_subset.empty:
                print(f"警告: 指标 {metric} 没有有效数据，跳过")
                continue

            # 创建箱型图
            fig_width = max(6, 1 * len(folder_names))  # 每组1宽度，最小6
            plt.figure(figsize=(fig_width, 8))

            # 使用seaborn创建更美观的箱型图
            sns.boxplot(data=df_subset, x="folder", y=metric, palette="Set2", width=0.3, whis=[0, 100])

            # 设置图表样式
            plt.title(f"{metric} box", fontsize=16, fontweight="bold", pad=20)
            plt.xlabel("")  # 不显示x轴标签
            plt.ylabel(metric, fontsize=14)
            plt.grid(True, alpha=0.3)

            # 旋转x轴标签以避免重叠
            plt.xticks(rotation=45, ha="right")
            
            # 调整布局
            plt.tight_layout()

            # 显示统计信息
            print(f"\n各文件夹 {metric} 统计信息:")
            print(df_subset.groupby("folder")[metric].describe())

            # 保存图片
            save_name = os.path.join(str(output_path), f"{metric}_regional.png")
            plt.savefig(save_name, dpi=300, bbox_inches="tight")
            print(f"\n图片已保存为: {save_name}")

            # 显示图片
            plt.show()

        return combined_df

    def create_metric_comparison_boxplot(self, folder_paths, output_path, folder_names=None, metric_names=None):
        """画出类似论文的箱型图，每个指标一个子图，每个子图里有不同folder的箱体
        
        Parameters:
        folder_paths: list, 包含多个文件夹路径的列表
        output_path: str, 输出图片的保存路径
        folder_names: list, 可选，文件夹的显示名称，如果不提供则使用文件夹名
        metric_names: list, 可选，指定要绘制的指标名（如["NSE", "RMSE"]），如果不提供则自动遍历所有数值型指标
        """
        # 确保输出目录存在
        self._ensure_output_dir(output_path)
        
        # 如果没有提供文件夹名称，则使用文件夹路径的最后一部分
        if folder_names is None:
            folder_names = [os.path.basename(path) for path in folder_paths]

        # 读取数据
        all_data = []
        for i, folder_path in enumerate(folder_paths):
            csv_path = os.path.join(folder_path, "metric_inflow.csv")
            df = self._load_csv_data(csv_path, folder=folder_names[i])
            if df is not None:
                all_data.append(df)

        if not all_data:
            print("错误: 没有成功读取任何数据")
            return None

        combined_df = pd.concat(all_data, ignore_index=True)

        # 自动检测指标
        if metric_names is None:
            metric_names = self._auto_detect_metrics(combined_df)
            
        if not metric_names:
            print("错误: 没有可用的指标名")
            return None

        n_metrics = len(metric_names)
        fig, axes = plt.subplots(1, n_metrics, figsize=(2.5 * n_metrics, 4), sharey=False)
        # 处理只有一个图的特殊情况
        if n_metrics == 1:
            axes = [axes]

        # 定义颜色
        palette = dict(zip(folder_names, self.colors[:len(folder_names)]))
        
        # 挨个画子图
        for ax, metric in zip(axes, metric_names):
            df_metric = combined_df[[metric, 'folder']].dropna()
            sns.boxplot(data=df_metric, x='folder', y=metric, ax=ax, palette=palette, width=0.5, whis=[0, 100])
            ax.set_xlabel(metric, fontsize=12, fontweight='bold')
            ax.set_ylabel('')
            ax.set_xticklabels([])  # 隐藏x轴的刻度标签
            ax.tick_params(axis='x', length=0) # 隐藏x轴的刻度线

        # 创建图例
        legend_elements = [Patch(facecolor=palette[name], label=name, edgecolor='black') for name in folder_names]
        fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), ncol=len(folder_names))

        plt.tight_layout(rect=[0, 0.03, 1, 0.90]) # 调整布局, 留出更多顶部空间给图例

        # 保存
        save_name = os.path.join(str(output_path), "metrics_comparison_subplots.png")
        plt.savefig(save_name, dpi=300)
        print(f"\n图片已保存为: {save_name}")
        plt.show()

        return combined_df

    def create_basin_nse_comparison_boxplot(self, folder_paths, output_path, basin_names=None, folder_names=None):
        """横坐标为流域，每个流域下有不同loss的NSE箱型图，适配每个loss方法一个csv（csv中有所有流域的NSE数据）的结构
        
        Parameters:
        folder_paths: list，每个元素为一个loss的文件夹（每个文件夹下有一个metric_inflow.csv，包含所有流域）
        output_path: str，输出图片保存路径
        basin_names: list，流域名称列表（用于横坐标显示），如果为None则自动检测
        folder_names: list，loss方法名称列表
        """
        # 确保输出目录存在
        self._ensure_output_dir(output_path)
        
        # 如果没有提供文件夹名称，则使用文件夹路径的最后一部分
        if folder_names is None:
            folder_names = [os.path.basename(path) for path in folder_paths]
            
        all_data = []
        basin_set = set()
        
        for i, folder_path in enumerate(folder_paths):
            csv_path = os.path.join(folder_path, "metric_inflow.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    # 检查流域标识列名
                    basin_col = None
                    for col in ["basin", "basin_id", "BASIN", "BASIN_ID"]:
                        if col in df.columns:
                            basin_col = col
                            break
                    if basin_col is None:
                        print(f"未找到流域标识列于 {csv_path}")
                        continue
                    df["basin"] = df[basin_col].astype(str)
                    basin_set.update(df["basin"].unique())
                    df["loss"] = folder_names[i]
                    all_data.append(df[["basin", "NSE", "loss"]])
                except Exception as e:
                    print(f"读取 {csv_path} 出错: {e}")
            else:
                print(f"文件不存在: {csv_path}")
                
        if not all_data:
            print("没有读取到任何数据！")
            return None
            
        plot_df = pd.concat(all_data, ignore_index=True)
        
        # 确定横坐标流域顺序
        if basin_names is None:
            basin_names = sorted(list(basin_set))
            
        # 绘图
        plt.figure(figsize=(max(8, 1.5*len(basin_names)), 6))
        sns.boxplot(data=plot_df, x="basin", y="NSE", hue="loss", order=basin_names, palette="Set2", width=0.5, whis=[0, 100])
        plt.xlabel("Basin", fontsize=14)
        plt.ylabel("NSE", fontsize=14)
        plt.title("NSE Comparison for Each Basin under Different Loss", fontsize=16, fontweight="bold", pad=20)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # 保存
        save_name = os.path.join(str(output_path), "basin_nse_loss_comparison.png")
        plt.savefig(save_name, dpi=300)
        print(f"\n图片已保存为: {save_name}")
        plt.show()
        
        return plot_df

    def merge_basin_data(self, basin_folders, method_folders):
        """合并单个流域数据

        Parameters:
        basin_folders: list, 流域文件夹路径列表
        method_folders: list, 每个流域下的方法文件夹名称列表 (如 ['method1', 'method2', 'method3'])

        Returns:
        dict: 按方法分组的合并数据
        """
        merged_data = {method: [] for method in method_folders}

        for basin_folder in basin_folders:
            basin_name = os.path.basename(basin_folder)
            print(f"Processing basin: {basin_name}")

            for method in method_folders:
                csv_path = os.path.join(f"{basin_folder}_{method}", "metric_inflow.csv")
                try:
                    df = pd.read_csv(csv_path)
                    if "NSE" in df.columns:
                        # 添加流域信息
                        df["basin"] = basin_name
                        df["method"] = method
                        df["data_type"] = "individual"  # 标记为单独流域数据
                        merged_data[method].append(
                            df[["basin_id", "NSE", "basin", "method", "data_type"]]
                        )
                        print(f"  - Successfully loaded {method}: {len(df)} records")
                    else:
                        print(f"  - Warning: No NSE column in {csv_path}")
                except FileNotFoundError:
                    print(f"  - File not found: {csv_path}")
                except Exception as e:
                    print(f"  - Error reading {csv_path}: {str(e)}")

        # 合并每个方法的数据
        for method in method_folders:
            if merged_data[method]:
                merged_data[method] = pd.concat(merged_data[method], ignore_index=True)
            else:
                merged_data[method] = pd.DataFrame()

        return merged_data

    def load_regional_data(self, regional_folder, method_folders):
        """加载regional数据

        Parameters:
        regional_folder: str, regional文件夹路径
        method_folders: list, 方法文件夹名称列表

        Returns:
        dict: 按方法分组的regional数据
        """
        regional_data = {}

        print("Processing Regional data:")
        for method in method_folders:
            csv_path = os.path.join(f"{regional_folder}_{method}", "metric_inflow.csv")
            try:
                df = pd.read_csv(csv_path)
                if "NSE" in df.columns:
                    df["method"] = method
                    df["data_type"] = "regional"  # 标记为regional数据
                    regional_data[method] = df[["basin_id", "NSE", "method", "data_type"]]
                    print(f"  - Successfully loaded {method}: {len(df)} records")
                else:
                    print(f"  - Warning: No NSE column in {csv_path}")
                    regional_data[method] = pd.DataFrame()
            except FileNotFoundError:
                print(f"  - File not found: {csv_path}")
                regional_data[method] = pd.DataFrame()
            except Exception as e:
                print(f"  - Error reading {csv_path}: {str(e)}")
                regional_data[method] = pd.DataFrame()

        return regional_data

    def create_comparison_boxplots(self, basin_folders, regional_folder, method_folders, method_names=None, save_plots=True, output_path=None):
        """创建比较箱型图：每个方法一个图，比较individual和regional

        Parameters:
        basin_folders: list, 流域文件夹路径列表
        regional_folder: str, regional文件夹路径
        method_folders: list, 方法文件夹名称列表
        method_names: list, 可选，方法的显示名称
        save_plots: bool, 是否保存图片
        output_path: str, 可选，输出路径，如果不提供则保存在当前目录
        """
        if method_names is None:
            method_names = method_folders

        # 合并流域数据
        print("=" * 50)
        print("Starting to merge basin data...")
        merged_basin_data = self.merge_basin_data(basin_folders, method_folders)

        # 加载regional数据
        print("=" * 50)
        print("Starting to load Regional data...")
        regional_data = self.load_regional_data(regional_folder, method_folders)

        # 为每个方法创建比较图
        print("=" * 50)
        print("Starting to generate boxplots...")

        for i, method in enumerate(method_folders):
            plt.figure(figsize=(10, 8))

            # 准备比较数据
            comparison_data = []

            # 添加合并的流域数据
            if not merged_basin_data[method].empty:
                basin_df = merged_basin_data[method].copy()
                basin_df["comparison_type"] = "Individual Basins"
                comparison_data.append(basin_df[["NSE", "comparison_type"]])

            # 添加regional数据
            if not regional_data[method].empty:
                regional_df = regional_data[method].copy()
                regional_df["comparison_type"] = "Regional"
                comparison_data.append(regional_df[["NSE", "comparison_type"]])

            if not comparison_data:
                print(f"Warning: No available data for {method}, skipping")
                plt.close()
                continue

            # 合并数据
            plot_data = pd.concat(comparison_data, ignore_index=True)

            # 创建箱型图
            sns.boxplot(
                data=plot_data,
                x="comparison_type",
                y="NSE",
                palette=["lightblue", "lightcoral"],
                width=0.2, 
                whis=[0, 100]
            )

            # 设置图表样式
            plt.title(
                f"{method_names[i]} - NSE Distribution Comparison",
                fontsize=16,
                fontweight="bold",
                pad=20,
            )
            plt.xlabel("Data Type", fontsize=14)
            plt.ylabel("NSE", fontsize=14)
            plt.grid(True, alpha=0.3)

            # 添加统计信息
            stats_text = ""
            for comp_type in plot_data["comparison_type"].unique():
                subset = plot_data[plot_data["comparison_type"] == comp_type]["NSE"]
                stats_text += f"{comp_type}:\n"
                stats_text += f"  Mean: {subset.mean():.3f}\n"
                stats_text += f"  Median: {subset.median():.3f}\n"
                stats_text += f"  Std: {subset.std():.3f}\n"
                stats_text += f"  Count: {len(subset)}\n\n"

            # 在图上添加统计信息
            plt.text(
                0.02,
                0.98,
                stats_text,
                transform=plt.gca().transAxes,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
                fontsize=10,
            )

            plt.tight_layout()

            # 保存图片
            if save_plots:
                if output_path is None:
                    filename = f"{method}_NSE_comparison.png"
                else:
                    self._ensure_output_dir(output_path)
                    filename = os.path.join(output_path, f"{method}_NSE_comparison.png")
                plt.savefig(filename, dpi=300, bbox_inches="tight")
                print(f"Saved plot: {filename}")

            plt.show()

            # 打印详细统计信息
            print(f"\n{method_names[i]} Statistical Summary:")
            print(plot_data.groupby("comparison_type")["NSE"].describe())
            print("-" * 30)
            
        return {"basin_data": merged_basin_data, "regional_data": regional_data}

    def create_combined_comparison_plot(self, basin_folder_paths, method_folders, output_path, method_names=None, metric_names=None, save_plot=True):
        """为多个流域创建类似论文的箱型图，汇总所有流域数据后，每个指标一个子图，对比不同方法/loss
        
        Parameters:
        basin_folder_paths: list, 流域文件夹路径列表
        method_folders: list, 方法文件夹名称列表
        output_path: str, 输出图片保存路径
        method_names: list, 可选，方法的显示名称
        metric_names: list, 可选，指定要绘制的指标名列表
        save_plot: bool, 是否保存图片
        """
        # 确保输出目录存在
        self._ensure_output_dir(output_path)
        
        if method_names is None:
            method_names = method_folders
        
        # 为多个流域加载所有loss的数据
        all_data = []
        print("Loading data for multiple basins...")
        for basin_path in basin_folder_paths:
            print(f"  -> Processing basin: {os.path.basename(basin_path)}")
            for i, method in enumerate(method_folders):
                csv_path = os.path.join(f"{basin_path}_{method}", "metric_inflow.csv")
                try:
                    df = pd.read_csv(csv_path)
                    df["method"] = method_names[i]
                    all_data.append(df)
                    print(f"    - Loaded {method} successfully.")
                except FileNotFoundError:
                    print(f"    - Warning: File not found, skipping: {csv_path}")
                except Exception as e:
                    print(f"    - Error reading {csv_path}: {str(e)}")

        if not all_data:
            print("Error: No data loaded. Please check paths.")
            return None

        combined_df = pd.concat(all_data, ignore_index=True)

        # 如果未提供，则自动检测指标
        if metric_names is None:
            metric_names = self._auto_detect_metrics(combined_df)
        
        if not metric_names:
            print("Error: No metric columns found to plot.")
            return None
            
        # 创建论文风格的箱型图
        n_metrics = len(metric_names)
        fig, axes = plt.subplots(1, n_metrics, figsize=(2.5 * n_metrics, 4), sharey=False)
        if n_metrics == 1:
            axes = [axes]

        palette = dict(zip(method_names, self.colors[:len(method_names)]))

        for ax, metric in zip(axes, metric_names):
            df_metric = combined_df[[metric, 'method']].dropna()
            sns.boxplot(data=df_metric, x='method', y=metric, ax=ax, palette=palette, width=0.5, whis=[0, 100])
            ax.set_xlabel(metric, fontsize=12, fontweight='bold')
            ax.set_ylabel('')
            ax.set_xticklabels([])
            ax.tick_params(axis='x', length=0)

        legend_elements = [Patch(facecolor=palette[name], label=name, edgecolor='black') for name in method_names]
        fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), ncol=len(method_names))

        plt.tight_layout(rect=[0, 0.03, 1, 0.90]) # 为图例留出空间

        if save_plot:
            save_name = os.path.join(output_path, "multi_basin_comparison.png")
            plt.savefig(save_name, dpi=300)
            print(f"\n图片已保存为: {save_name}")

        plt.show()

        return combined_df

    def create_metric_individual_vs_regional_boxplot(self, basin_folders, regional_folder, method_folder, method_name=None, metric_names=None, save_plot=True, output_path=None):
        """每个指标一个子图（subplot），每个子图上是individual和regional两个箱型图
        
        Parameters:
        basin_folders: list, 流域文件夹路径列表
        regional_folder: str, regional文件夹路径
        method_folder: str, 方法文件夹名称（如'weighted_mse_loss'）
        method_name: str, 可选，方法显示名称
        metric_names: list, 可选，指标名列表
        save_plot: bool, 是否保存图片
        output_path: str, 可选，图片保存路径
        """
        # 确保输出目录存在
        if output_path is not None:
            self._ensure_output_dir(output_path)
            
        # 合并individual数据
        all_basin_data = []
        for basin_folder in basin_folders:
            csv_path = os.path.join(f"{basin_folder}_{method_folder}", "metric_inflow.csv")
            try:
                df = pd.read_csv(csv_path)
                df["data_type"] = "Individual"
                all_basin_data.append(df)
            except Exception as e:
                print(f"读取 {csv_path} 出错: {e}")
                
        if not all_basin_data:
            print("没有读取到任何individual数据！")
            return None
            
        basin_df = pd.concat(all_basin_data, ignore_index=True)
        
        # 加载regional数据
        regional_path = os.path.join(f"{regional_folder}_{method_folder}", "metric_inflow.csv")
        try:
            regional_df = pd.read_csv(regional_path)
            regional_df["data_type"] = "Regional"
        except Exception as e:
            print(f"读取 {regional_path} 出错: {e}")
            return None
            
        # 合并数据
        combined_df = pd.concat([basin_df, regional_df], ignore_index=True)
        
        # 自动检测指标
        if metric_names is None:
            metric_names = self._auto_detect_metrics(combined_df)
            
        if not metric_names:
            print("没有可用的指标名！")
            return None
            
        n_metrics = len(metric_names)
        fig, axes = plt.subplots(1, n_metrics, figsize=(2.5 * n_metrics, 5), sharey=False)
        if n_metrics == 1:
            axes = [axes]
            
        for ax, metric in zip(axes, metric_names):
            df_metric = combined_df[[metric, 'data_type']].dropna()
            sns.boxplot(data=df_metric, x='data_type', y=metric, ax=ax, palette=self.individual_regional_palette, width=0.5, whis=[0, 100])
            ax.set_xlabel(metric, fontsize=12, fontweight='bold')
            ax.set_ylabel('')
            ax.set_xticklabels(["Individual", "Regional"], fontsize=11)
            ax.tick_params(axis='x', length=0)
            
        # 图例
        legend_elements = [Patch(facecolor=self.individual_regional_palette[name], label=name, edgecolor='black') for name in self.individual_regional_palette]
        fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), ncol=2)
        plt.suptitle(f"{method_name or method_folder} - Individual vs Regional for Each Metric", fontsize=16, fontweight="bold", y=1.03)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # 保存
        if save_plot:
            if output_path is None:
                output_path = "."
            save_name = os.path.join(output_path, f"{method_folder}_metric_individual_vs_regional_subplots.png")
            plt.savefig(save_name, dpi=300, bbox_inches="tight")
            print(f"\n图片已保存为: {save_name}")
            
        plt.show()
        return combined_df


# 使用示例
def example_usage():
    """使用示例"""
    # 创建工具实例
    tool = BasinBoxplotTool()
    
    # 示例1: 从多个文件夹创建箱型图
    folder_paths = [
        "D:\\Project\\Hydro\\plot\\events_train_3h\\regional_weighted_mse_loss",
        "D:\\Project\\Hydro\\plot\\events_train_3h\\regional_weighted_hybrid_loss",
        "D:\\Project\\Hydro\\plot\\events_train_3h\\regional_hybrid_loss",
    ]
    folder_names = ["Weighted_MSE", "Weighted_Hybrid", "Hybrid"]
    metric_names = ["NSE", "RMSE", "KGE", "FHV", "FLV"]
    output_path = "D:\\Project\\Hydro\\plot\\plt\\regional_loss_3h"
    
    # 生成单个箱型图
    # tool.create_boxplot_from_folders(folder_paths, output_path, folder_names, metric_names)
    
    # 示例2: 生成指标对比箱型图
    # tool.create_metric_comparison_boxplot(folder_paths, output_path, folder_names, metric_names)
    
    # 示例3: 生成流域NSE对比箱型图
    # tool.create_basin_nse_comparison_boxplot(folder_paths, output_path, None, folder_names)
    
    # 示例4: 创建individual vs regional比较
    basin_folders = [
        "events_train/songliao_20800900",
        "events_train/songliao_20810200",
        "events_train/songliao_21100150",
        "events_train/songliao_21110150",
        "events_train/songliao_21401050",
        "events_train/songliao_21401550",
    ]
    regional_folder = "events_train/regional"
    method_folders = ["weighted_mse_loss", "weighted_hybrid_loss", "hybrid_loss"]
    method_names = ["Weighted MSE", "Weighted Hybrid", "Hybrid"]
    
    # 创建比较箱型图
    # tool.create_comparison_boxplots(
    #     basin_folders, regional_folder, method_folders, method_names, 
    #     save_plots=True, output_path="plt/single_basin_comparison"
    # )
    
    # 示例5: 创建单个方法的individual vs regional指标对比图
    # tool.create_metric_individual_vs_regional_boxplot(
    #     basin_folders=basin_folders,
    #     regional_folder=regional_folder,
    #     method_folder="hybrid_loss",
    #     method_name="Hybrid Loss",
    #     metric_names=metric_names,
    #     save_plot=True,
    #     output_path="plt/compare_1D"
    # )
    
    # 示例6: 创建多流域多方法的指标对比图
    # tool.create_combined_comparison_plot(
    #     basin_folder_paths=basin_folders,
    #     method_folders=method_folders,
    #     output_path="plt/multi_basin_comparison",
    #     method_names=method_names,
    #     metric_names=metric_names
    # )
    
    print("示例完成，请取消注释需要运行的函数。")


if __name__ == "__main__":
    example_usage()