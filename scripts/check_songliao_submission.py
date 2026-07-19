from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


DEFAULT_EXPERIMENT = "songliao_event_3h"
DEFAULT_BASIN = "songliao_21401550"


def status(ok: bool) -> str:
    return "[OK]" if ok else "[FAIL]"


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def check_path(label: str, path: Path, root: Path, required: bool = True) -> bool:
    exists = path.exists()
    prefix = status(exists) if required else ("[OK]" if exists else "[WARN]")
    print(f"{prefix} {label}: {rel(path, root)}")
    return exists or not required


def read_metrics(path: Path, basin: str) -> dict[str, float] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            row_basin = row.get("") or row.get("basin") or row.get("station_id")
            if row_basin == basin:
                values: dict[str, float] = {}
                for key, value in row.items():
                    if key and value not in (None, ""):
                        try:
                            values[key] = float(value)
                        except ValueError:
                            continue
                return values
    return None


def read_calibration(path: Path, basin: str) -> tuple[float | None, dict[str, object]]:
    if not path.exists():
        return None, {}
    with path.open("r", encoding="utf-8") as file:
        basin_data = json.load(file).get(basin, {})
    return basin_data.get("objective_value"), basin_data.get("algorithm_info", {})


def find_figures_dir(result_dir: Path, basin: str) -> Path:
    base = result_dir / "evaluation_test" / "figures"
    basin_dir = base / basin
    return basin_dir if basin_dir.exists() else base


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Songliao outputs without rerunning calibration."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    parser.add_argument("--basin", default=DEFAULT_BASIN)
    parser.add_argument("--nse-threshold", type=float, default=0.55)
    parser.add_argument("--min-flood-events", type=int, default=1)
    parser.add_argument(
        "--report",
        action="append",
        default=[],
        metavar="PATH",
        help="Report file to require. Repeat for multiple files.",
    )
    parser.add_argument(
        "--pr-file",
        action="append",
        default=[],
        metavar="PATH",
        help="PR or issue material to require. Repeat for multiple files.",
    )
    parser.add_argument(
        "--require-fdc",
        action="store_true",
        help="Treat a missing flow-duration curve as a failure instead of a warning.",
    )
    return parser


def print_metrics(values: dict[str, float] | None, threshold: float) -> bool:
    if values is None:
        print("[FAIL] metrics row not found")
        return False

    ok = True
    for name in ("NSE", "KGE", "RMSE", "Corr"):
        value = values.get(name)
        if value is None:
            print(f"[FAIL] {name}: missing")
            ok = False
        else:
            print(f"[OK] {name}: {value:.6f}")

    nse = values.get("NSE")
    if nse is None or nse < threshold:
        print(f"[FAIL] NSE is below threshold {threshold}")
        return False
    print(f"[OK] NSE reaches threshold {threshold}")
    return ok


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    result_dir = root / "hydromodel" / "results" / "songliao_event" / args.experiment
    config = root / "hydromodel" / "configs" / f"{args.experiment}.yaml"
    calibration = result_dir / "calibration_results.json"
    metrics_path = result_dir / "evaluation_test" / "basins_metrics.csv"
    denorm = result_dir / "evaluation_test" / "basins_denorm_params.csv"
    figures = find_figures_dir(result_dir, args.basin)
    scatter = figures / f"{args.basin}_scatter.png"
    fdc = figures / f"{args.basin}_fdc.png"
    flood_dir = figures / "flood_events"
    flood_count = len(list(flood_dir.glob("*.png"))) if flood_dir.exists() else 0

    print("Songliao submission audit")
    print("=" * 72)
    print(f"Root       : {root}")
    print(f"Experiment : {args.experiment}")
    print(f"Basin      : {args.basin}")
    print()

    core_ok = True
    core_ok &= check_path("model config", config, root)
    core_ok &= check_path("calibration results", calibration, root)
    core_ok &= check_path("metrics csv", metrics_path, root)
    core_ok &= check_path("denormalized params csv", denorm, root)
    core_ok &= check_path("figures directory", figures, root)
    core_ok &= check_path("scatter figure", scatter, root)
    core_ok &= check_path("flow duration curve figure", fdc, root, args.require_fdc)
    core_ok &= check_path("flood event figures directory", flood_dir, root)
    enough_events = flood_count >= args.min_flood_events
    print(f"{status(enough_events)} flood event figure count: {flood_count}")
    core_ok &= enough_events
    print()

    objective, algorithm = read_calibration(calibration, args.basin)
    if objective is None:
        print("[FAIL] objective_value not found")
        core_ok = False
    else:
        print(f"[OK] objective_value: {objective:.6f}")
    if algorithm:
        print(
            "[OK] algorithm_info: "
            f"rep={algorithm.get('rep')}, ngs={algorithm.get('ngs')}, "
            f"random_seed={algorithm.get('random_seed')}"
        )
    else:
        print("[WARN] algorithm_info not found")
    print()

    core_ok &= print_metrics(read_metrics(metrics_path, args.basin), args.nse_threshold)

    requested_ok = True
    requested_files = [("report", value) for value in args.report]
    requested_files += [("PR material", value) for value in args.pr_file]
    if requested_files:
        print()
        print("Requested submission files")
        for label, value in requested_files:
            path = Path(value)
            if not path.is_absolute():
                path = root / path
            requested_ok &= check_path(label, path, root)
    else:
        print()
        print("[INFO] No report or PR files requested; auditing model outputs only.")

    print()
    if core_ok and requested_ok:
        print("[OK] Requested submission package is complete.")
        return 0
    print("[FAIL] Submission package is incomplete.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
