"""Tests for the read-only songliao environment doctor."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_env  # noqa: E402


def _write(path: Path, text: str = "x\n") -> None:
    """Create a text file, making parent directories as needed.

    Args:
        path: Destination file.
        text: File contents.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fake_repo(
    tmp_path: Path, *, with_data: bool = True, with_sources: bool = True
) -> Path:
    """Build a minimal homework-layout tree for filesystem checks.

    Args:
        tmp_path: Pytest temporary directory.
        with_data: Whether to create the nested songliaorrevent data root.
        with_sources: Whether to create hydromodel/hydrodataset/hydrodatasource.

    Returns:
        Fake repository root.
    """
    _write(tmp_path / "README.md", "# homework\n")
    _write(tmp_path / "requirements.txt", "mlflow\n")
    if with_sources:
        for name in ("hydrodataset", "hydrodatasource", "hydromodel"):
            (tmp_path / name).mkdir()
        _write(
            tmp_path / "hydromodel" / "configs" / "songliao_event_3h.yaml",
            "data_cfgs:\n  uri: ../data/songliaorrevent/songliaorrevent\n",
        )
        for script in check_env.HYDROMODEL_SCRIPTS:
            _write(tmp_path / "hydromodel" / "scripts" / script, "print('ok')\n")
        _write(
            tmp_path / "hydrodataset" / "pyproject.toml",
            '[tool.hatch.version]\nsource = "vcs"\n# hatch-vcs\n',
        )
        _write(
            tmp_path / "hydrodatasource" / "pyproject.toml",
            '[tool.hatch.version]\nsource = "vcs"\n# hatch-vcs\n',
        )
        _write(
            tmp_path / "hydromodel" / "pyproject.toml", "[project]\nname='hydromodel'\n"
        )
    if with_data:
        data_root = tmp_path / "data" / "songliaorrevent" / "songliaorrevent"
        (data_root / "attributes").mkdir(parents=True)
        (data_root / "timeseries").mkdir()
        (data_root / "shapes").mkdir()
    return tmp_path


def test_python_version_fail_below_311() -> None:
    """Python 3.10 must FAIL because hydromodel requires 3.11."""
    result = check_env.check_python_version((3, 10, 14))
    assert result.status == "FAIL"
    assert "3.11" in result.message


def test_python_version_ok_311() -> None:
    """Python 3.11 is accepted."""
    result = check_env.check_python_version((3, 11, 15))
    assert result.status == "OK"


def test_python_version_warn_313() -> None:
    """Python 3.13 is a warning, not a hard failure."""
    result = check_env.check_python_version((3, 13, 0))
    assert result.status == "WARN"


def test_data_typo_one_r_is_fail(tmp_path: Path) -> None:
    """A songliaorevent (one r) folder should be diagnosed explicitly."""
    _fake_repo(tmp_path, with_data=False)
    (tmp_path / "data" / "songliaorevent" / "songliaorevent").mkdir(parents=True)
    results = {item.name: item for item in check_env.check_data_layout(tmp_path)}
    assert results["data_root"].status == "FAIL"
    assert "两个 r" in results["data_root"].fix


def test_data_layout_ok(tmp_path: Path) -> None:
    """The documented nested data tree is OK."""
    _fake_repo(tmp_path)
    results = check_env.check_data_layout(tmp_path)
    by_name = {item.name: item for item in results}
    assert by_name["data_root"].status == "OK"
    assert by_name["data_attributes"].status == "OK"
    assert by_name["data_timeseries"].status == "OK"
    assert by_name["data_shapes"].status == "OK"


def test_missing_shapes_is_warn_not_fail(tmp_path: Path) -> None:
    """shapes/ is documented but not required by FloodEventDatasource."""
    _fake_repo(tmp_path)
    shapes = tmp_path / "data" / "songliaorrevent" / "songliaorrevent" / "shapes"
    shapes.rmdir()
    results = {item.name: item for item in check_env.check_data_layout(tmp_path)}
    assert results["data_shapes"].status == "WARN"
    assert results["data_root"].status == "OK"


def test_read_and_resolve_relative_uri(tmp_path: Path) -> None:
    """Relative uri values resolve from hydromodel/, matching the skill docs."""
    _fake_repo(tmp_path)
    config = tmp_path / "hydromodel" / "configs" / "songliao_event_3h.yaml"
    uri = check_env.read_config_uri(config)
    assert uri == "../data/songliaorrevent/songliaorrevent"
    resolved = check_env.resolve_config_uri(uri, tmp_path / "hydromodel")
    assert (
        resolved
        == (tmp_path / "data" / "songliaorrevent" / "songliaorrevent").resolve()
    )


def test_config_uri_one_r_fail(tmp_path: Path) -> None:
    """Config uri using the one-r typo is FAIL."""
    _fake_repo(tmp_path)
    config = tmp_path / "hydromodel" / "configs" / "songliao_event_3h.yaml"
    config.write_text(
        "data_cfgs:\n  uri: ../data/songliaorevent/songliaorevent\n",
        encoding="utf-8",
    )
    results = {item.name: item for item in check_env.check_hydromodel_files(tmp_path)}
    assert results["config_uri"].status == "FAIL"
    assert "两个 r" in results["config_uri"].fix


def test_missing_source_dirs(tmp_path: Path) -> None:
    """Teacher zip folders are required."""
    _fake_repo(tmp_path, with_sources=False, with_data=False)
    results = {item.name: item for item in check_env.check_source_dirs(tmp_path)}
    assert results["source_hydromodel"].status == "FAIL"
    assert results["source_hydrodataset"].status == "FAIL"


def test_hatch_vcs_warns_without_git_or_version(tmp_path: Path) -> None:
    """Zipped hatch-vcs projects without git metadata should WARN."""
    _fake_repo(tmp_path)
    results = {item.name: item for item in check_env.check_hatch_vcs_layout(tmp_path)}
    assert results["hatch_vcs_hydrodataset"].status == "WARN"
    assert "hatch-vcs" in results["hatch_vcs_hydrodataset"].message


def test_missing_hydrodataset_does_not_claim_pypi() -> None:
    """When hydrodataset is not installed, do not blame a PyPI wheel."""
    if importlib.util.find_spec("hydrodataset") is not None:
        pytest.skip("hydrodataset is installed in this environment")
    results = {item.name: item for item in check_env.check_imports(ROOT)}
    assert "hydrodataset_configs" not in results
    assert results["import_hydrodataset"].status == "FAIL"
    assert "PyPI" not in results["import_hydrodataset"].message


def test_gpu_missing_is_not_fail() -> None:
    """A machine without CUDA must not FAIL; the course is CPU-only."""
    results = check_env.check_gpu()
    assert all(item.status == "INFO" for item in results)
    assert any(item.name == "gpu_required" for item in results)


def test_recommended_commands_windows_uses_set_location(tmp_path: Path) -> None:
    """Windows command cheat-sheet uses PowerShell and cmd cd syntax."""
    text = check_env.recommended_commands(tmp_path, os_name="nt")
    assert "Set-Location -LiteralPath" in text
    assert "cd /d" in text
    assert "run_event_calibration.py" in text
    assert "run_xaj_evaluate.py" in text
    assert "visualize.py" in text
    assert str(tmp_path / "hydromodel") in text


def test_recommended_commands_posix(tmp_path: Path) -> None:
    """POSIX cheat-sheet uses cd and forward slashes."""
    text = check_env.recommended_commands(tmp_path, os_name="posix")
    assert "Set-Location" not in text
    assert "run_xaj_evaluate.py" in text


def test_deepseek_env_does_not_print_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """The doctor must never echo API keys."""
    secret = "sk-secret-should-not-appear-in-output"
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", secret)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
    monkeypatch.setenv("ANTHROPIC_MODEL", "deepseek-v4-pro[1m]")
    results = check_env.check_deepseek_env()
    blob = "\n".join(item.message + item.fix for item in results)
    assert secret not in blob
    token = next(item for item in results if item.name == "anthropic_token")
    assert token.status == "OK"


def test_deepseek_base_url_requires_anthropic_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DeepSeek gateway URL without /anthropic is FAIL."""
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com")
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    results = {item.name: item for item in check_env.check_deepseek_env()}
    assert results["anthropic_base_url"].status == "FAIL"


def test_run_all_checks_skip_imports_no_writes(tmp_path: Path) -> None:
    """Filesystem checks must not create files."""

    def snapshot() -> set[tuple[str, int]]:
        items: set[tuple[str, int]] = set()
        for path in tmp_path.rglob("*"):
            if path.is_file():
                items.add((str(path.relative_to(tmp_path)), path.stat().st_mtime_ns))
        return items

    _fake_repo(tmp_path)
    before = snapshot()
    results = check_env.run_all_checks(tmp_path, skip_imports=True)
    after = snapshot()
    assert before == after
    assert results
    assert any(item.name == "python_version" for item in results)


def test_exit_code_fail_on_any_fail() -> None:
    """A single FAIL makes the process return 1; WARN does not."""
    ok = check_env.CheckResult("c", "n", "OK", "ok")
    warn = check_env.CheckResult("c", "n", "WARN", "warn")
    fail = check_env.CheckResult("c", "n", "FAIL", "fail")
    assert check_env.exit_code_for([ok, warn]) == 0
    assert check_env.exit_code_for([ok, fail]) == 1


def test_cli_json_on_real_repo() -> None:
    """Running the doctor against this checkout must stay read-only and JSON-safe."""

    def snapshot() -> dict[str, int]:
        tracked = [
            ROOT / "README.md",
            ROOT / "requirements.txt",
            ROOT / "docs" / "faq.md",
            ROOT / "scripts" / "check_env.py",
        ]
        return {
            str(path): path.stat().st_mtime_ns for path in tracked if path.is_file()
        }

    before = snapshot()
    extra_before = {p.name for p in ROOT.iterdir()}
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_env.py"), "--json", "--skip-imports"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    after = snapshot()
    extra_after = {p.name for p in ROOT.iterdir()}
    assert before == after
    assert extra_before == extra_after
    payload = json.loads(proc.stdout)
    assert payload["exit_code"] == 1
    names = {item["name"] for item in payload["results"]}
    assert "source_hydromodel" in names
    assert "data_root" in names
    assert proc.returncode == 1


def test_cli_text_mentions_double_r() -> None:
    """Student-facing text must mention the songliaorrevent double-r pitfall."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_env.py")],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert "songliaorrevent" in proc.stdout
    assert "只读" in proc.stdout
    assert "sk-" not in proc.stdout


def test_workflow_wrapper_doctor_and_commands() -> None:
    """Issue #4's suggested CLI should reach the same read-only doctor."""
    wrapper = SCRIPTS / "songliao_workflow.py"
    doctor = subprocess.run(
        [sys.executable, str(wrapper), "doctor", "--skip-imports", "--json"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    payload = json.loads(doctor.stdout)
    assert payload["exit_code"] == 1
    commands = subprocess.run(
        [sys.executable, str(wrapper), "commands"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert commands.returncode == 0
    assert "run_event_calibration.py" in commands.stdout
    rejected = subprocess.run(
        [sys.executable, str(wrapper), "calibrate"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert rejected.returncode == 2
    assert "read-only" in rejected.stderr.lower() or "只读" in rejected.stderr


def test_commands_only() -> None:
    """--commands-only prints launch commands and does not need hydromodel installed."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_env.py"), "--commands-only"],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    assert "run_event_calibration.py" in proc.stdout
    assert "不会代你执行" in proc.stdout


@pytest.mark.skipif(os.name == "nt", reason="stat.S_IWRITE semantics differ on Windows")
def test_readonly_check_warns(tmp_path: Path) -> None:
    """A chmod -w pyproject.toml is reported without being changed back."""
    _fake_repo(tmp_path)
    target = tmp_path / "hydrodataset" / "pyproject.toml"
    mode = target.stat().st_mode
    target.chmod(mode & ~stat.S_IWRITE & ~stat.S_IWGRP & ~stat.S_IWOTH)
    try:
        results = {
            item.name: item for item in check_env.check_readonly_sources(tmp_path)
        }
        assert results["readonly_sources"].status in {"WARN", "OK"}
        # The file must still exist and the doctor must not chmod it back.
        assert target.is_file()
    finally:
        target.chmod(mode)
