from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BASIN = "songliao_21401550"


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def create_result(root: Path, name: str, nse: float) -> None:
    result = root / "hydromodel" / "results" / "songliao_event" / name
    evaluation = result / "evaluation_test"
    figures = evaluation / "figures" / BASIN
    flood = figures / "flood_events"
    flood.mkdir(parents=True)
    (root / "hydromodel" / "configs").mkdir(parents=True, exist_ok=True)
    (root / "hydromodel" / "configs" / f"{name}.yaml").write_text(
        "model_cfgs:\n  name: xaj_mz\n  params:\n    kernel_size: 9\n",
        encoding="utf-8",
    )
    with (evaluation / "basins_metrics.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["", "NSE", "KGE", "RMSE", "Corr", "Bias", "FHV", "FLV"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "": BASIN,
                "NSE": nse,
                "KGE": 0.67,
                "RMSE": 2.1,
                "Corr": 0.76,
                "Bias": -0.4,
                "FHV": -20,
                "FLV": -30,
            }
        )
    (evaluation / "basins_denorm_params.csv").write_text("basin,K\n", encoding="utf-8")
    (result / "calibration_results.json").write_text(
        json.dumps(
            {
                BASIN: {
                    "objective_value": 1.9,
                    "algorithm_info": {"rep": 8000, "ngs": 10, "random_seed": 1234},
                }
            }
        ),
        encoding="utf-8",
    )
    (figures / f"{BASIN}_scatter.png").write_bytes(b"png")
    (flood / "event.png").write_bytes(b"png")


class ComparisonTests(unittest.TestCase):
    def test_collect_sorts_by_nse_and_writes_relative_paths(self) -> None:
        module = load_script("comparison_tool", "scripts/compare_songliao_experiments.py")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_result(root, "lower", 0.50)
            create_result(root, "higher", 0.60)
            results = root / "hydromodel" / "results" / "songliao_event"
            experiments = module.collect(root, results, BASIN)
            self.assertEqual([item.name for item in experiments], ["higher", "lower"])
            output = root / "reports" / "comparison.csv"
            module.write_csv(output, experiments, root)
            with output.open(encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertFalse(Path(rows[0]["result_dir"]).is_absolute())


class CommandTests(unittest.TestCase):
    def test_workflow_calibration_dry_run(self) -> None:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "songliao_workflow.py"),
                "calibrate",
                "--dry-run",
            ],
            cwd=REPO,
            env=env,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("configs/songliao_event_3h.yaml", proc.stdout)

    def test_submission_audit_accepts_complete_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_result(root, "songliao_event_3h", 0.56)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "scripts" / "check_songliao_submission.py"),
                    "--root",
                    str(root),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertIn("Requested submission package is complete", proc.stdout)

    def test_submission_audit_rejects_requested_missing_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_result(root, "songliao_event_3h", 0.56)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "scripts" / "check_songliao_submission.py"),
                    "--root",
                    str(root),
                    "--report",
                    "missing.docx",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()
