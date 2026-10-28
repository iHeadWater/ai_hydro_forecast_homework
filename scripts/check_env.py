#!/usr/bin/env python3
"""Read-only environment doctor for the songliao homework repository.

This script never installs packages, never writes files, and never changes
system settings. It only inspects the current interpreter, filesystem, and
environment variables, then prints OK/WARN/FAIL with suggested fixes.

Run from anywhere::

    python scripts/check_env.py

On Windows you can also use the PowerShell wrapper ``scripts/check_env.ps1``.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

MIN_PYTHON = (3, 11)
RECOMMENDED_CONDA_ENV = "hydro_homework"
DATA_NESTED = Path("data") / "songliaorrevent" / "songliaorrevent"
DATA_TYPO_ONE_R = Path("data") / "songliaorevent"
REQUIRED_DATA_SUBDIRS = ("attributes", "timeseries")
OPTIONAL_DATA_SUBDIRS = ("shapes",)
SOURCE_DIRS = ("hydrodataset", "hydrodatasource", "hydromodel")
REQUIRED_MODULES = ("hydromodel", "hydrodatasource", "hydrodataset", "hydroutils")
HYDROMODEL_SCRIPTS = (
    "run_event_calibration.py",
    "run_xaj_evaluate.py",
    "visualize.py",
)
DEFAULT_CONFIG = Path("hydromodel") / "configs" / "songliao_event_3h.yaml"
DEFAULT_BASIN = "songliao_21401550"
DEFAULT_EXPERIMENT = "songliao_event_3h"
MARKER_FILES = ("README.md", "requirements.txt")


@dataclass(frozen=True)
class CheckResult:
    """One doctor check and the text a student should read.

    Attributes:
        category: Grouping label printed as a section header.
        name: Short check id, unique within a run.
        status: One of OK, WARN, FAIL, INFO.
        message: What was observed.
        fix: Actionable next step. Empty when nothing needs doing.
    """

    category: str
    name: str
    status: str
    message: str
    fix: str = ""


def find_repo_root(explicit: Path | None = None) -> Path:
    """Resolve the homework repository root.

    Args:
        explicit: Optional path from ``--root``. When omitted, walk from this
            file's parent directory and from the current working directory.

    Returns:
        Directory that contains README.md and requirements.txt.

    Raises:
        FileNotFoundError: If no candidate looks like this repository.
    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser().resolve())
    candidates.append(Path(__file__).resolve().parents[1])
    candidates.append(Path.cwd().resolve())
    here = Path.cwd().resolve()
    candidates.extend(here.parents)

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if all((candidate / marker).is_file() for marker in MARKER_FILES):
            return candidate
    raise FileNotFoundError(
        "Could not find the homework repo root (README.md + requirements.txt)."
    )


def _result(
    category: str,
    name: str,
    status: str,
    message: str,
    fix: str = "",
) -> CheckResult:
    """Build a CheckResult with stripped message text.

    Args:
        category: Section name.
        name: Check id.
        status: OK, WARN, FAIL, or INFO.
        message: Observation shown to the student.
        fix: Optional suggested fix.

    Returns:
        A populated check result.
    """
    return CheckResult(category, name, status, message.strip(), fix.strip())


def check_python_version(version_info: tuple[int, ...] | None = None) -> CheckResult:
    """Check that the running interpreter meets hydromodel's requirement.

    Args:
        version_info: A ``sys.version_info``-like tuple. Defaults to the
            current interpreter.

    Returns:
        FAIL when Python is older than 3.11. WARN on 3.13+ because some
        scientific stacks (for example numba) may lag.
    """
    info = version_info if version_info is not None else sys.version_info
    version = f"{info[0]}.{info[1]}.{info[2] if len(info) > 2 else 0}"
    if (info[0], info[1]) < MIN_PYTHON:
        return _result(
            "Python",
            "python_version",
            "FAIL",
            f"当前 Python 是 {version}，hydromodel 要求 >= 3.11。",
            "请新建环境: conda create -n hydro_homework python=3.11 && "
            "conda activate hydro_homework",
        )
    if (info[0], info[1]) >= (3, 13):
        return _result(
            "Python",
            "python_version",
            "WARN",
            f"当前 Python 是 {version}。课程按 3.11 编写，3.13+ 上 numba 等"
            "依赖可能尚未提供对应轮子。",
            "若安装失败，请改用: conda create -n hydro_homework python=3.11",
        )
    return _result(
        "Python",
        "python_version",
        "OK",
        f"Python {version} 满足 >= 3.11。",
    )


def check_interpreter(conda_env: str | None = None) -> list[CheckResult]:
    """Report the current executable and whether a conda env is active.

    Args:
        conda_env: Value of CONDA_DEFAULT_ENV. Defaults to the real env var.

    Returns:
        Interpreter path, conda env name, and a PyCharm hint when relevant.
    """
    results: list[CheckResult] = []
    executable = sys.executable
    results.append(
        _result(
            "Python",
            "interpreter",
            "OK",
            f"当前解释器: {executable}",
        )
    )
    env_name = (
        conda_env if conda_env is not None else os.environ.get("CONDA_DEFAULT_ENV")
    )
    if env_name:
        if env_name == RECOMMENDED_CONDA_ENV:
            results.append(
                _result(
                    "Python",
                    "conda_env",
                    "OK",
                    f"已激活 conda 环境: {env_name}",
                )
            )
        else:
            results.append(
                _result(
                    "Python",
                    "conda_env",
                    "WARN",
                    f"当前 conda 环境是 {env_name}，文档推荐的名字是 "
                    f"{RECOMMENDED_CONDA_ENV}。",
                    f"conda activate {RECOMMENDED_CONDA_ENV}   "
                    "# 若你自己建了别的名字且依赖已装齐，可以忽略此警告",
                )
            )
    else:
        prefix = sys.prefix
        in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        if in_venv:
            results.append(
                _result(
                    "Python",
                    "conda_env",
                    "INFO",
                    f"未检测到 CONDA_DEFAULT_ENV，但当前处于虚拟环境: {prefix}",
                )
            )
        else:
            results.append(
                _result(
                    "Python",
                    "conda_env",
                    "WARN",
                    "看起来像系统 Python，而不是课程虚拟环境。",
                    "conda create -n hydro_homework python=3.11 && "
                    "conda activate hydro_homework",
                )
            )

    lower_exe = executable.lower()
    if "pycharm" in lower_exe or "jetbrains" in lower_exe:
        results.append(
            _result(
                "Python",
                "pycharm_interpreter",
                "FAIL",
                "当前解释器路径像是 PyCharm 自带/错误的解释器。",
                "在 PyCharm 中选择 conda 环境 hydro_homework 的 python.exe；"
                "运行 hydromodel 脚本时把 Working directory 设为仓库里的 "
                "hydromodel 目录。",
            )
        )
    return results


def check_source_dirs(root: Path) -> list[CheckResult]:
    """Check that teacher-provided source trees sit next to this repo.

    Args:
        root: Homework repository root.

    Returns:
        One result per expected source directory.
    """
    results: list[CheckResult] = []
    for name in SOURCE_DIRS:
        path = root / name
        if path.is_dir():
            results.append(
                _result(
                    "源码目录",
                    f"source_{name}",
                    "OK",
                    f"已找到 {name}/",
                )
            )
        else:
            results.append(
                _result(
                    "源码目录",
                    f"source_{name}",
                    "FAIL",
                    f"缺少 {name}/ 。本仓库不自带这份源码。",
                    "把老师发的压缩包解压到仓库根目录，使 hydrodataset/、"
                    "hydrodatasource/、hydromodel/ 与 README.md 同级。",
                )
            )
    return results


def _looks_like_one_r_typo(root: Path) -> Path | None:
    """Return a path that looks like the songliaorevent (one r) typo.

    Args:
        root: Homework repository root.

    Returns:
        The mistaken directory if it exists, otherwise None.
    """
    typo = root / DATA_TYPO_ONE_R
    if typo.exists():
        return typo
    # Also catch a single-level data/songliaorevent or unzip-in-place folder.
    for candidate in (
        root / "songliaorevent",
        root / "data" / "songliaorevent",
    ):
        if candidate.exists():
            return candidate
    return None


def check_data_layout(root: Path) -> list[CheckResult]:
    """Check the local songliao flood-event data tree.

    Args:
        root: Homework repository root.

    Returns:
        Results for the nested data directory and required subfolders.
        ``shapes/`` is documented but not required by FloodEventDatasource.
    """
    results: list[CheckResult] = []
    data_root = root / DATA_NESTED
    typo = _looks_like_one_r_typo(root)

    if data_root.is_dir():
        results.append(
            _result(
                "数据",
                "data_root",
                "OK",
                f"已找到数据根目录 {DATA_NESTED.as_posix()} "
                "（目录名是 songliaorrevent，两个 r）。",
            )
        )
    else:
        fix = (
            "解压老师发的数据包到仓库根目录，最终必须是 "
            "data/songliaorrevent/songliaorrevent/ "
            "（注意是两个 r，不是 songliaorevent）。内层这一级才是数据根，"
            "里面应有 attributes/ 和 timeseries/。"
        )
        if typo is not None:
            rel = _rel(typo, root)
            fix = (
                f"检测到可能的错误目录名: {rel} 。正确名字是 "
                "songliaorrevent（两个 r）。请把文件夹放到 "
                "data/songliaorrevent/songliaorrevent/ 。"
            )
        results.append(
            _result(
                "数据",
                "data_root",
                "FAIL",
                f"未找到 {DATA_NESTED.as_posix()} 。",
                fix,
            )
        )
        return results

    for subdir in REQUIRED_DATA_SUBDIRS:
        path = data_root / subdir
        if path.is_dir():
            results.append(
                _result(
                    "数据",
                    f"data_{subdir}",
                    "OK",
                    f"已找到 {subdir}/",
                )
            )
        else:
            results.append(
                _result(
                    "数据",
                    f"data_{subdir}",
                    "FAIL",
                    f"数据根下缺少 {subdir}/ 。FloodEventDatasource 需要它。",
                    "确认压缩包是否完整解压；内层 songliaorrevent 目录里应有 "
                    "attributes/ 与 timeseries/。",
                )
            )
    for subdir in OPTIONAL_DATA_SUBDIRS:
        path = data_root / subdir
        if path.is_dir():
            results.append(
                _result(
                    "数据",
                    f"data_{subdir}",
                    "OK",
                    f"已找到 {subdir}/（文档中的可选目录）。",
                )
            )
        else:
            results.append(
                _result(
                    "数据",
                    f"data_{subdir}",
                    "WARN",
                    f"数据根下没有 {subdir}/ 。文档示例里有这一级，"
                    "读取器当前只强制要求 attributes/ 和 timeseries/。",
                    "若率定能跑就先忽略；若报 shapefile 相关错误，再向老师确认"
                    "数据包是否完整。",
                )
            )
    return results


def read_config_uri(config_path: Path) -> str | None:
    """Extract the ``uri:`` value from a YAML config without PyYAML.

    Args:
        config_path: Path to songliao_event_3h.yaml or similar.

    Returns:
        The raw uri string, or None when the file is missing or has no uri.
    """
    if not config_path.is_file():
        return None
    text = config_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?m)^\s*uri:\s*(.+)$", text)
    if not match:
        return None
    raw = match.group(1).split("#", 1)[0].strip().strip("'\"")
    return raw or None


def resolve_config_uri(uri: str, hydromodel_dir: Path) -> Path:
    """Resolve a config uri against the hydromodel directory.

    Args:
        uri: Value of data_cfgs.uri.
        hydromodel_dir: ``<repo>/hydromodel``.

    Returns:
        Absolute path. Relative uris are resolved from hydromodel/, matching
        how the calibration scripts are meant to be launched.
    """
    path = Path(uri)
    if path.is_absolute():
        return path
    return (hydromodel_dir / path).resolve()


def check_hydromodel_files(root: Path) -> list[CheckResult]:
    """Check calibration/eval/visualize scripts and the default config.

    Args:
        root: Homework repository root.

    Returns:
        Existence checks plus a uri sanity check when the config is present.
    """
    results: list[CheckResult] = []
    hydro = root / "hydromodel"
    if not hydro.is_dir():
        return results

    for script in HYDROMODEL_SCRIPTS:
        path = hydro / "scripts" / script
        if path.is_file():
            results.append(
                _result(
                    "hydromodel 脚本",
                    f"script_{script}",
                    "OK",
                    f"已找到 hydromodel/scripts/{script}",
                )
            )
        else:
            results.append(
                _result(
                    "hydromodel 脚本",
                    f"script_{script}",
                    "FAIL",
                    f"缺少 hydromodel/scripts/{script} 。",
                    "确认解压的是老师提供的 hydromodel，而不是空目录或旧拷贝。",
                )
            )

    config_path = root / DEFAULT_CONFIG
    if not config_path.is_file():
        results.append(
            _result(
                "配置",
                "config_yaml",
                "FAIL",
                f"缺少 {DEFAULT_CONFIG.as_posix()} 。",
                "该文件在老师提供的 hydromodel 里。不要改 time_unit / reader / "
                "is_event_data；作业用的流域是碧流河 songliao_21401550。",
            )
        )
        return results

    results.append(
        _result(
            "配置",
            "config_yaml",
            "OK",
            f"已找到 {DEFAULT_CONFIG.as_posix()}",
        )
    )
    uri = read_config_uri(config_path)
    if not uri:
        results.append(
            _result(
                "配置",
                "config_uri",
                "WARN",
                "配置文件里没有读到 uri 字段。",
                "打开 hydromodel/configs/songliao_event_3h.yaml，确认 "
                "data_cfgs.uri 指向 ../data/songliaorrevent/songliaorrevent "
                "（相对 hydromodel/ 目录）。",
            )
        )
        return results

    if re.search(r"songliaorevent(?!r)", uri.replace("\\", "/")):
        results.append(
            _result(
                "配置",
                "config_uri",
                "FAIL",
                f"配置 uri 写成了 songliaorevent（一个 r）: {uri}",
                "改成 songliaorrevent（两个 r），例如 "
                "uri: ../data/songliaorrevent/songliaorrevent",
            )
        )
        return results

    resolved = resolve_config_uri(uri, hydro)
    expected = (root / DATA_NESTED).resolve()
    if resolved.is_dir():
        note = f"配置 uri 可解析: {uri} -> {resolved}"
        if expected.is_dir() and resolved != expected:
            results.append(
                _result(
                    "配置",
                    "config_uri",
                    "WARN",
                    note + f" ，与文档默认数据目录 {expected} 不是同一处。",
                    "只要该路径确实是老师发的 songliao 数据即可；"
                    "否则改成 ../data/songliaorrevent/songliaorrevent 并从 "
                    "hydromodel/ 目录运行脚本。",
                )
            )
        else:
            results.append(_result("配置", "config_uri", "OK", note))
    else:
        rel_hint = "../data/songliaorrevent/songliaorrevent"
        results.append(
            _result(
                "配置",
                "config_uri",
                "FAIL",
                f"配置 uri 指向的路径不存在: {uri} （解析为 {resolved}）",
                f"在 hydromodel/configs/songliao_event_3h.yaml 把 uri 改成 "
                f"{rel_hint} ，并且始终从 hydromodel/ 目录运行率定脚本。"
                "不要从仓库根目录或 PyCharm 默认 working directory 直接跑。",
            )
        )
    return results


def _is_under(path: Path, parent: Path) -> bool:
    """Return True if path is inside parent.

    Args:
        path: File or directory to test.
        parent: Expected ancestor.

    Returns:
        True when path is parent or a descendant of parent.
    """
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def check_imports(root: Path) -> list[CheckResult]:
    """Check required packages import and come from the local editable trees.

    Args:
        root: Homework repository root.

    Returns:
        Import and location results. A PyPI hydrodataset (no configs module)
        is treated as FAIL.
    """
    results: list[CheckResult] = []
    hydrodataset_imported = False
    missing_hint = (
        "先 conda activate hydro_homework，在仓库根目录执行 "
        "python -m pip install -r requirements.txt 。"
        "若报 ModuleNotFoundError: editables、Unknown version source: vcs "
        "或 PermissionError 写不了 _version.py，请看 docs/faq.md 的安装一节："
        "pip install --upgrade pip setuptools wheel && "
        "pip install hatchling hatch-vcs editables && "
        "pip install -r requirements.txt --no-build-isolation"
    )
    for module_name in REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - doctor must show any import error
            results.append(
                _result(
                    "依赖导入",
                    f"import_{module_name}",
                    "FAIL",
                    f"无法 import {module_name}: {type(exc).__name__}: {exc}",
                    missing_hint,
                )
            )
            continue
        if module_name == "hydrodataset":
            hydrodataset_imported = True
        location = Path(getattr(module, "__file__", "") or "").resolve()
        expected_dir = root / (
            "hydrodataset"
            if module_name == "hydrodataset"
            else (
                "hydrodatasource"
                if module_name == "hydrodatasource"
                else "hydromodel" if module_name == "hydromodel" else ""
            )
        )
        if module_name in SOURCE_DIRS and expected_dir.is_dir():
            if _is_under(location, expected_dir):
                results.append(
                    _result(
                        "依赖导入",
                        f"import_{module_name}",
                        "OK",
                        f"import {module_name} 成功，来自本地源码: {location}",
                    )
                )
            else:
                results.append(
                    _result(
                        "依赖导入",
                        f"import_{module_name}",
                        "FAIL",
                        f"import {module_name} 成功，但加载的不是仓库里的源码: "
                        f"{location}",
                        "这通常是装了 PyPI 版。请确认仓库根目录有这份源码后，"
                        "在已激活的环境里重新执行 python -m pip install -r "
                        "requirements.txt （requirements.txt 使用 -e ./ 本地安装）。",
                    )
                )
        else:
            results.append(
                _result(
                    "依赖导入",
                    f"import_{module_name}",
                    "OK",
                    f"import {module_name} 成功: {location}",
                )
            )

    if hydrodataset_imported:
        try:
            importlib.import_module("hydrodataset.configs")
            results.append(
                _result(
                    "依赖导入",
                    "hydrodataset_configs",
                    "OK",
                    "hydrodataset.configs 可以导入（说明不是缺模块的 PyPI 旧包）。",
                )
            )
        except ModuleNotFoundError:
            results.append(
                _result(
                    "依赖导入",
                    "hydrodataset_configs",
                    "FAIL",
                    "hydrodataset 能导入，但没有 hydrodataset.configs。"
                    "几乎可以肯定装的是 PyPI 版，它还会拉来不兼容的 aqua_fetch。",
                    "删除当前环境中的 hydrodataset 后，用老师提供的本地 "
                    "hydrodataset/ 再执行 python -m pip install -r requirements.txt",
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                _result(
                    "依赖导入",
                    "hydrodataset_configs",
                    "WARN",
                    f"导入 hydrodataset.configs 时出现: {type(exc).__name__}: {exc}",
                    missing_hint,
                )
            )
    return results


def check_hatch_vcs_layout(root: Path) -> list[CheckResult]:
    """Warn when local packages look hard to build with hatch-vcs.

    Args:
        root: Homework repository root.

    Returns:
        WARN when a hatch-vcs project has neither git metadata nor _version.py.
    """
    results: list[CheckResult] = []
    for name in ("hydrodataset", "hydrodatasource"):
        pkg_root = root / name
        if not pkg_root.is_dir():
            continue
        version_py = pkg_root / name / "_version.py"
        has_git = (pkg_root / ".git").exists()
        pyproject = pkg_root / "pyproject.toml"
        uses_hatch_vcs = False
        if pyproject.is_file():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            uses_hatch_vcs = "hatch-vcs" in text
        if uses_hatch_vcs and not has_git and not version_py.is_file():
            results.append(
                _result(
                    "安装",
                    f"hatch_vcs_{name}",
                    "WARN",
                    f"{name}/ 用了 hatch-vcs 管理版本，但既没有 .git 也没有 "
                    f"{name}/_version.py。从压缩包解压时 pip 可能报 "
                    "Unknown version source: vcs。",
                    "先 pip install hatchling hatch-vcs editables，再 "
                    "pip install -r requirements.txt --no-build-isolation 。"
                    "若仍失败，把完整报错发给老师/助教。",
                )
            )
        elif uses_hatch_vcs:
            results.append(
                _result(
                    "安装",
                    f"hatch_vcs_{name}",
                    "OK",
                    f"{name}/ 的版本文件或 git 元数据看起来可用于 hatch-vcs。",
                )
            )
    return results


def check_readonly_sources(root: Path) -> list[CheckResult]:
    """Detect read-only teacher zip files that break pip on Windows.

    Args:
        root: Homework repository root.

    Returns:
        WARN when a representative source file is not writable. The check
        never clears the read-only bit.
    """
    samples = [
        root / "hydrodataset" / "pyproject.toml",
        root / "hydrodatasource" / "pyproject.toml",
        root / "hydromodel" / "pyproject.toml",
    ]
    blocked = [
        path for path in samples if path.is_file() and not os.access(path, os.W_OK)
    ]
    if not blocked:
        existing = [path for path in samples if path.is_file()]
        if not existing:
            return []
        return [
            _result(
                "安装",
                "readonly_sources",
                "OK",
                "抽查的源码文件可写（未发现只读属性）。",
            )
        ]
    listed = ", ".join(_rel(path, root) for path in blocked)
    return [
        _result(
            "安装",
            "readonly_sources",
            "WARN",
            f"以下文件当前不可写: {listed} 。Windows 下从压缩包解压时有时会带"
            "只读属性，pip 写 _version.py 会 PermissionError。",
            "在资源管理器取消只读，或把项目拷到当前用户可写的目录后再装。"
            "本检测脚本不会帮你改文件属性。",
        )
    ]


def check_encoding() -> list[CheckResult]:
    """Check stdout encoding and UTF-8 related environment variables.

    Returns:
        FAIL when the console encoding cannot represent BMP characters
        (typical Windows cp936/cp1252 issue with emoji in hydromodel logs).
    """
    results: list[CheckResult] = []
    encoding = getattr(sys.stdout, "encoding", None) or ""
    pythonutf8 = os.environ.get("PYTHONUTF8", "")
    ioencoding = os.environ.get("PYTHONIOENCODING", "")
    results.append(
        _result(
            "编码",
            "stdout_encoding",
            "OK" if encoding.lower().startswith("utf") else "WARN",
            f"stdout encoding={encoding or 'unknown'}, PYTHONUTF8={pythonutf8 or '(未设置)'}, "
            f"PYTHONIOENCODING={ioencoding or '(未设置)'}",
            (
                ""
                if encoding.lower().startswith("utf")
                else "Windows 下率定脚本若打印 emoji 可能 UnicodeEncodeError。"
                "在运行脚本前执行: set PYTHONUTF8=1 "
                "(cmd) 或 $env:PYTHONUTF8='1' (PowerShell)，然后重开终端。"
            ),
        )
    )
    return results


def check_non_ascii_path(root: Path) -> CheckResult:
    """Warn when the repo path contains non-ASCII characters.

    Args:
        root: Homework repository root.

    Returns:
        WARN on non-ASCII paths, which historically break some Windows tools.
    """
    text = str(root)
    if text.isascii():
        return _result(
            "编码",
            "repo_path_ascii",
            "OK",
            f"仓库路径不含非 ASCII 字符: {root}",
        )
    return _result(
        "编码",
        "repo_path_ascii",
        "WARN",
        f"仓库路径含中文或其他非 ASCII 字符: {root}",
        "若后续出现乱码或找不到文件，把仓库放到纯英文路径后再试，例如 "
        "C:\\hydro\\ai_hydro_forecast_homework",
    )


def check_cache_dir() -> CheckResult:
    """Report whether the hydrodataset cache directory exists.

    Returns:
        INFO/WARN only. This doctor never creates the cache directory.
    """
    home = Path.home()
    cache = home / ".cache" / "hydrodataset"
    if cache.is_dir():
        return _result(
            "缓存",
            "hydrodataset_cache",
            "OK",
            f"缓存目录已存在: {cache}",
        )
    return _result(
        "缓存",
        "hydrodataset_cache",
        "INFO",
        f"尚未发现缓存目录 {cache} 。新机器第一次跑很常见。",
        "老师提供的 hydrodatasource 一般会自动创建该目录。若仍报 "
        "FileNotFoundError: ...\\.cache\\hydrodataset\\...attributes.nc，"
        "说明装的不是带补丁的本地包；不要用本脚本去建目录，先重装本地源码。"
        "Windows 上临时手工创建（可选）: "
        'New-Item -ItemType Directory -Force "$env:USERPROFILE\\.cache\\hydrodataset"',
    )


def check_hydro_setting() -> CheckResult:
    """hydro_setting.yml is only needed for MinIO, not local course data.

    Returns:
        INFO whether the file exists. Missing is not a failure.
    """
    setting = Path.home() / "hydro_setting.yml"
    if setting.is_file():
        return _result(
            "配置",
            "hydro_setting",
            "INFO",
            f"发现 {setting} 。本课程用本地 data/ ，一般不需要 MinIO 配置。",
        )
    return _result(
        "配置",
        "hydro_setting",
        "INFO",
        "未找到 ~/hydro_setting.yml 。本地 songliao 数据不需要这个文件；"
        "提示 Configuration file not found 可以忽略。",
    )


def _run_version_command(argv: list[str]) -> str | None:
    """Run a short version command and return stripped stdout.

    Args:
        argv: Command and arguments.

    Returns:
        stdout on success, otherwise None. Never raises.
    """
    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or proc.stderr or "").strip() or None


def check_gpu() -> list[CheckResult]:
    """Report GPU/CUDA availability as information, not a requirement.

    Returns:
        INFO results. Conceptual XAJ + SCE-UA does not need a GPU. Missing
        CUDA is never FAIL.
    """
    results = [
        _result(
            "GPU",
            "gpu_required",
            "INFO",
            "本课程率定是概念性 XAJ + SCE-UA，在 CPU 上运行，不需要 GPU/CUDA。",
        )
    ]
    nvidia = shutil.which("nvidia-smi")
    if nvidia is None:
        results.append(
            _result(
                "GPU",
                "nvidia_smi",
                "INFO",
                "未找到 nvidia-smi（没有 NVIDIA 驱动或未加入 PATH）。对课程无影响。",
            )
        )
    else:
        detail = _run_version_command(
            [nvidia, "--query-gpu=name,driver_version", "--format=csv,noheader"]
        )
        results.append(
            _result(
                "GPU",
                "nvidia_smi",
                "INFO",
                f"检测到 NVIDIA GPU: {detail or nvidia} 。课程仍不要求使用它。",
            )
        )
    torch_spec = importlib.util.find_spec("torch")
    if torch_spec is None:
        results.append(
            _result(
                "GPU",
                "torch",
                "INFO",
                "未安装 PyTorch。课程默认流程不需要 torch。",
            )
        )
        return results
    try:
        import torch  # type: ignore

        cuda_ok = bool(torch.cuda.is_available())
        results.append(
            _result(
                "GPU",
                "torch",
                "INFO",
                f"检测到 torch {torch.__version__}，cuda_available={cuda_ok}。"
                "默认 XAJ 率定不会用到它。",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(
            _result(
                "GPU",
                "torch",
                "INFO",
                f"import torch 失败（可忽略）: {type(exc).__name__}: {exc}",
            )
        )
    return results


def check_node() -> CheckResult:
    """Check Node.js because Claude Code requires Node >= 18.

    Returns:
        WARN when node is missing or too old. This is not a Python FAIL.
    """
    node = shutil.which("node")
    if node is None:
        return _result(
            "AI Agent",
            "nodejs",
            "WARN",
            "未找到 node。要用 Claude Code 需要 Node.js >= 18。",
            "安装 Node.js: https://nodejs.org/zh-cn/download/ 后新开终端，"
            "再 npm install -g @anthropic-ai/claude-code 。详见 docs/setup.md。",
        )
    version_text = _run_version_command([node, "-v"]) or ""
    match = re.search(r"v?(\d+)", version_text)
    major = int(match.group(1)) if match else 0
    if major and major < 18:
        return _result(
            "AI Agent",
            "nodejs",
            "WARN",
            f"Node.js 版本是 {version_text}，Claude Code 需要 >= 18。",
            "请安装更新的 Node.js LTS，然后重开终端。",
        )
    return _result(
        "AI Agent",
        "nodejs",
        "OK",
        f"Node.js {version_text or node} 可用于安装 Claude Code。",
    )


def check_deepseek_env() -> list[CheckResult]:
    """Check DeepSeek-for-Claude-Code environment variables without leaking secrets.

    Returns:
        WARN when the documented variables are missing. The token value is
        never printed.
    """
    results: list[CheckResult] = []
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    token_set = bool(os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip())
    model = os.environ.get("ANTHROPIC_MODEL", "")

    if not base_url:
        results.append(
            _result(
                "AI Agent",
                "anthropic_base_url",
                "WARN",
                "未设置 ANTHROPIC_BASE_URL。若你用 DeepSeek 驱动 Claude Code，"
                "当前终端还没配好。",
                "必须设为 https://api.deepseek.com/anthropic （末尾 /anthropic "
                "不能少）。完整 8 个变量见 docs/claude-code-deepseek.md 与 "
                "docs/faq.md。",
            )
        )
    elif not base_url.rstrip("/").endswith("/anthropic"):
        results.append(
            _result(
                "AI Agent",
                "anthropic_base_url",
                "FAIL",
                f"ANTHROPIC_BASE_URL={base_url} ，末尾缺少 /anthropic。",
                "改成 https://api.deepseek.com/anthropic 后重开 Claude Code。",
            )
        )
    else:
        results.append(
            _result(
                "AI Agent",
                "anthropic_base_url",
                "OK",
                "ANTHROPIC_BASE_URL 以 /anthropic 结尾。",
            )
        )

    if token_set:
        results.append(
            _result(
                "AI Agent",
                "anthropic_token",
                "OK",
                "ANTHROPIC_AUTH_TOKEN 已设置（检测脚本不会打印密钥）。",
            )
        )
    else:
        results.append(
            _result(
                "AI Agent",
                "anthropic_token",
                "WARN",
                "未设置 ANTHROPIC_AUTH_TOKEN。只有在用 DeepSeek/第三方转发时才需要。",
                "在 DeepSeek 开放平台创建 API key，赋给 ANTHROPIC_AUTH_TOKEN，"
                "不要带 <>，也不要把 key 写进要提交的文件。",
            )
        )

    if model:
        results.append(
            _result(
                "AI Agent",
                "anthropic_model",
                "INFO",
                f"ANTHROPIC_MODEL={model}",
                "模型名以 docs/claude-code-deepseek.md 为准；官方若改名请看该文档。"
                "不要把模型名随手写成 gpt 或 claude-3 之类。",
            )
        )
    else:
        results.append(
            _result(
                "AI Agent",
                "anthropic_model",
                "INFO",
                "未设置 ANTHROPIC_MODEL。若走 DeepSeek，请按 "
                "docs/claude-code-deepseek.md 配置一整组变量。",
            )
        )
    return results


def check_cwd(root: Path, cwd: Path | None = None) -> CheckResult:
    """Warn when the current working directory is a common footgun.

    Args:
        root: Homework repository root.
        cwd: Current working directory. Defaults to Path.cwd().

    Returns:
        INFO/WARN about where the student is running the doctor from.
        Calibration scripts still need to be launched from hydromodel/.
    """
    current = (cwd or Path.cwd()).resolve()
    hydro = (root / "hydromodel").resolve()
    if current == root.resolve():
        return _result(
            "工作目录",
            "cwd",
            "OK",
            "当前在仓库根目录。环境检测从这里跑没问题；"
            "率定/评估脚本仍要 cd 到 hydromodel/ 再运行。",
        )
    if current == hydro:
        return _result(
            "工作目录",
            "cwd",
            "OK",
            "当前在 hydromodel/ 目录，适合直接运行率定脚本。",
        )
    return _result(
        "工作目录",
        "cwd",
        "WARN",
        f"当前工作目录是 {current} ，既不是仓库根也不是 hydromodel/。",
        "检测脚本会按仓库根来找文件。跑率定前请切换到 hydromodel/："
        "PowerShell: Set-Location -LiteralPath '<repo>\\hydromodel' ；"
        "cmd/Anaconda Prompt: cd /d <repo>\\hydromodel",
    )


def recommended_commands(root: Path, os_name: str | None = None) -> str:
    """Return copy-paste commands for the current operating system.

    Args:
        root: Homework repository root.
        os_name: ``os.name`` override for tests (``nt`` or ``posix``).

    Returns:
        Multi-line text. Commands are printed only; nothing is executed.
    """
    name = os_name if os_name is not None else os.name
    hydro = root / "hydromodel"
    config = f"configs/{DEFAULT_EXPERIMENT}.yaml"
    cal_dir = f"results/songliao_event/{DEFAULT_EXPERIMENT}"
    eval_dir = f"{cal_dir}/evaluation_test"
    lines = [
        "以下命令只打印、不会代你执行（本工具保持只读）：",
        "",
        f"conda activate {RECOMMENDED_CONDA_ENV}",
        "",
    ]
    if name == "nt":
        lines.extend(
            [
                "cmd / Anaconda Prompt:",
                f'  cd /d "{root}"',
                "  python scripts\\check_env.py",
                f'  cd /d "{hydro}"',
                f"  python scripts\\run_event_calibration.py --config {config}",
                "  python scripts\\run_xaj_evaluate.py "
                f"--calibration-dir {cal_dir} --eval-period test",
                "  python scripts\\visualize.py "
                f"--eval-dir {eval_dir} --basins {DEFAULT_BASIN} --plot-types all",
                "",
                "PowerShell:",
                f"  Set-Location -LiteralPath '{root}'",
                "  python scripts\\check_env.py",
                "  # 或: .\\scripts\\check_env.ps1",
                f"  Set-Location -LiteralPath '{hydro}'",
                f"  python scripts\\run_event_calibration.py --config {config}",
                "  python scripts\\run_xaj_evaluate.py "
                f"--calibration-dir {cal_dir} --eval-period test",
                "  python scripts\\visualize.py "
                f"--eval-dir {eval_dir} --basins {DEFAULT_BASIN} --plot-types all",
            ]
        )
    else:
        lines.extend(
            [
                f'cd "{root}"',
                "python scripts/check_env.py",
                f'cd "{hydro}"',
                f"python scripts/run_event_calibration.py --config {config}",
                "python scripts/run_xaj_evaluate.py "
                f"--calibration-dir {cal_dir} --eval-period test",
                "python scripts/visualize.py "
                f"--eval-dir {eval_dir} --basins {DEFAULT_BASIN} --plot-types all",
            ]
        )
    lines.extend(
        [
            "",
            "注意: 率定只产出 RMSE；NSE 在评估步骤的 basins_metrics.csv 里。",
            f"作业流域是碧流河 {DEFAULT_BASIN}。请勿修改配置里的验证期 test_period。",
        ]
    )
    return "\n".join(lines)


def run_all_checks(root: Path, *, skip_imports: bool = False) -> list[CheckResult]:
    """Run every read-only check against ``root``.

    Args:
        root: Homework repository root.
        skip_imports: When True, skip importlib checks. Used by filesystem
            unit tests so they do not depend on a fully installed env.

    Returns:
        Ordered list of check results.
    """
    results: list[CheckResult] = []
    results.append(check_python_version())
    results.extend(check_interpreter())
    results.append(check_cwd(root))
    results.extend(check_source_dirs(root))
    results.extend(check_data_layout(root))
    results.extend(check_hydromodel_files(root))
    results.extend(check_hatch_vcs_layout(root))
    results.extend(check_readonly_sources(root))
    if not skip_imports:
        results.extend(check_imports(root))
    results.extend(check_encoding())
    results.append(check_non_ascii_path(root))
    results.append(check_cache_dir())
    results.append(check_hydro_setting())
    results.extend(check_gpu())
    results.append(check_node())
    results.extend(check_deepseek_env())
    return results


def exit_code_for(results: Iterable[CheckResult]) -> int:
    """Return process exit code.

    Args:
        results: Check results.

    Returns:
        1 if any FAIL is present, otherwise 0. WARN does not fail the process
        so students can still use a usable-but-imperfect environment.
    """
    return 1 if any(item.status == "FAIL" for item in results) else 0


def _rel(path: Path, root: Path) -> str:
    """Pretty-print path relative to the repo when possible.

    Args:
        path: File or directory.
        root: Repository root.

    Returns:
        Relative posix-ish string, or the original path.
    """
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def format_report(results: list[CheckResult], root: Path) -> str:
    """Render a student-facing report.

    Args:
        results: Check results.
        root: Repository root (printed in the header).

    Returns:
        Multi-line report. Status tags stay ASCII so Windows cp936 consoles
        can still display the labels even when Chinese text is garbled.
    """
    counts = {key: 0 for key in ("OK", "WARN", "FAIL", "INFO")}
    for item in results:
        counts[item.status] = counts.get(item.status, 0) + 1

    lines = [
        "Songliao 环境自检（只读，不会改你的系统、不会装包、不会写文件）",
        "=" * 72,
        f"仓库根目录 : {root}",
        f"当前目录   : {Path.cwd()}",
        f"操作系统   : {platform.system()} {platform.release()} ({os.name})",
        f"解释器     : {sys.executable}",
        f"Python     : {platform.python_version()}",
        "",
    ]
    current_category = None
    for item in results:
        if item.category != current_category:
            current_category = item.category
            lines.append(f"[{item.category}]")
        tag = f"[{item.status}]"
        lines.append(f"  {tag:<7} {item.message}")
        if item.fix:
            lines.append(f"          -> {item.fix}")
    lines.extend(
        [
            "",
            "-" * 72,
            f"汇总: {counts['FAIL']} FAIL, {counts['WARN']} WARN, "
            f"{counts['OK']} OK, {counts['INFO']} INFO",
            "",
            recommended_commands(root),
            "",
            "更多说明见 docs/faq.md 。",
        ]
    )
    return "\n".join(lines)


def configure_stdio() -> None:
    """Best-effort UTF-8 stdio for this process only.

    Reconfiguring the current streams is not a system modification; it only
    affects this doctor process so Chinese text is less likely to crash
    Windows consoles.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list. Defaults to sys.argv[1:].

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Read-only environment doctor for the songliao homework. "
            "Does not install packages, write files, or change system settings."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Homework repository root (default: auto-detect).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of the text report.",
    )
    parser.add_argument(
        "--skip-imports",
        action="store_true",
        help="Skip import checks (used in filesystem tests).",
    )
    parser.add_argument(
        "--commands-only",
        action="store_true",
        help="Only print recommended calibrate/evaluate/visualize commands.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the doctor and return an exit code.

    Args:
        argv: Optional argument list.

    Returns:
        1 when any FAIL is present, otherwise 0.
    """
    configure_stdio()
    args = parse_args(argv)
    try:
        root = find_repo_root(args.root)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        print(
            "          -> 请在仓库根目录运行: python scripts/check_env.py",
            file=sys.stderr,
        )
        return 1

    if args.commands_only:
        print(recommended_commands(root))
        return 0

    results = run_all_checks(root, skip_imports=args.skip_imports)
    if args.json:
        payload = {
            "root": str(root),
            "executable": sys.executable,
            "python": platform.python_version(),
            "results": [asdict(item) for item in results],
            "exit_code": exit_code_for(results),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report(results, root))
    return exit_code_for(results)


if __name__ == "__main__":
    raise SystemExit(main())
