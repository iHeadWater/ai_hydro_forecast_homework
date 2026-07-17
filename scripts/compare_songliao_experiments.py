from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


METRIC_FIELDS = ["NSE", "KGE", "RMSE", "Corr", "Bias", "FHV", "FLV"]


def rel(path: Path | None, root: Path) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


@dataclass
class ExperimentResult:
    name: str
    result_dir: Path
    config_path: Path | None
    objective_value: float | None
    rep: int | None
    ngs: int | None
    random_seed: int | None
    model_name: str | None
    kernel_size: int | None
    metrics: dict[str, float]
    figure_count: int
    flood_event_count: int

    @property
    def nse(self) -> float:
        return self.metrics.get("NSE", float("-inf"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Songliao calibration/evaluation experiments without rerunning models."
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--basin", default="songliao_21401550", help="Basin id to compare.")
    parser.add_argument(
        "--results-dir",
        default="hydromodel/results/songliao_event",
        help="Directory containing experiment result folders.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for generated comparison CSV/Markdown.",
    )
    parser.add_argument("--no-write", action="store_true", help="Only print comparison table.")
    return parser.parse_args()


def read_metrics(path: Path, basin: str) -> dict[str, float]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_basin = row.get("") or row.get("basin") or row.get("station_id")
            if row_basin == basin:
                values: dict[str, float] = {}
                for field in METRIC_FIELDS:
                    if row.get(field) not in (None, ""):
                        values[field] = float(row[field])
                return values
    return {}


def read_calibration(path: Path, basin: str) -> tuple[float | None, int | None, int | None, int | None]:
    if not path.exists():
        return None, None, None, None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    basin_data = data.get(basin, {})
    info = basin_data.get("algorithm_info", {})
    return (
        basin_data.get("objective_value"),
        info.get("rep"),
        info.get("ngs"),
        info.get("random_seed"),
    )


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def parse_config_hint(path: Path | None) -> tuple[str | None, int | None]:
    if path is None or not path.exists():
        return None, None
    text = path.read_text(encoding="utf-8", errors="ignore")
    model_match = re.search(r"(?m)^\s*name:\s*([A-Za-z0-9_]+)\s*$", text)
    kernel_match = re.search(r"(?m)^\s*kernel_size:\s*(\d+)\s*$", text)
    model = model_match.group(1) if model_match else None
    kernel = int(kernel_match.group(1)) if kernel_match else None
    return model, kernel


def count_figures(result_dir: Path, basin: str) -> tuple[int, int]:
    figures_root = result_dir / "evaluation_test" / "figures"
    basin_figures = figures_root / basin
    if basin_figures.exists():
        figures_root = basin_figures
    if not figures_root.exists():
        return 0, 0
    all_png = list(figures_root.rglob("*.png"))
    flood_dir = figures_root / "flood_events"
    flood_png = list(flood_dir.glob("*.png")) if flood_dir.exists() else []
    return len(all_png), len(flood_png)


def collect(root: Path, results_dir: Path, basin: str) -> list[ExperimentResult]:
    experiments: list[ExperimentResult] = []
    if not results_dir.exists():
        return experiments
    for result_dir in sorted(path for path in results_dir.iterdir() if path.is_dir()):
        metrics_path = result_dir / "evaluation_test" / "basins_metrics.csv"
        metrics = read_metrics(metrics_path, basin)
        if not metrics:
            continue

        objective, rep, ngs, random_seed = read_calibration(result_dir / "calibration_results.json", basin)
        config = first_existing(
            [
                result_dir / "calibration_config.yaml",
                root / "hydromodel" / "configs" / f"{result_dir.name}.yaml",
            ]
        )
        model_name, kernel_size = parse_config_hint(config)
        figure_count, flood_event_count = count_figures(result_dir, basin)
        experiments.append(
            ExperimentResult(
                name=result_dir.name,
                result_dir=result_dir,
                config_path=config,
                objective_value=objective,
                rep=rep,
                ngs=ngs,
                random_seed=random_seed,
                model_name=model_name,
                kernel_size=kernel_size,
                metrics=metrics,
                figure_count=figure_count,
                flood_event_count=flood_event_count,
            )
        )
    return sorted(experiments, key=lambda item: item.nse, reverse=True)


def fmt(value: object, digits: int = 6) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def row(exp: ExperimentResult) -> list[str]:
    return [
        exp.name,
        fmt(exp.metrics.get("NSE")),
        fmt(exp.metrics.get("KGE")),
        fmt(exp.metrics.get("RMSE")),
        fmt(exp.metrics.get("Corr")),
        fmt(exp.objective_value),
        fmt(exp.rep, 0),
        fmt(exp.ngs, 0),
        fmt(exp.random_seed, 0),
        exp.model_name or "-",
        fmt(exp.kernel_size, 0),
        str(exp.figure_count),
        str(exp.flood_event_count),
    ]


def print_table(experiments: list[ExperimentResult]) -> None:
    headers = [
        "experiment",
        "NSE",
        "KGE",
        "RMSE",
        "Corr",
        "objective",
        "rep",
        "ngs",
        "seed",
        "model",
        "kernel",
        "figures",
        "events",
    ]
    rows = [headers] + [row(exp) for exp in experiments]
    widths = [max(len(items[i]) for items in rows) for i in range(len(headers))]
    for idx, items in enumerate(rows):
        line = "  ".join(item.ljust(widths[i]) for i, item in enumerate(items))
        print(line)
        if idx == 0:
            print("  ".join("-" * width for width in widths))


def write_csv(path: Path, experiments: list[ExperimentResult], root: Path) -> None:
    headers = [
        "experiment",
        "NSE",
        "KGE",
        "RMSE",
        "Corr",
        "Bias",
        "FHV",
        "FLV",
        "objective_value",
        "rep",
        "ngs",
        "random_seed",
        "model",
        "kernel_size",
        "figure_count",
        "flood_event_count",
        "result_dir",
        "config_path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for exp in experiments:
            writer.writerow(
                {
                    "experiment": exp.name,
                    "NSE": exp.metrics.get("NSE"),
                    "KGE": exp.metrics.get("KGE"),
                    "RMSE": exp.metrics.get("RMSE"),
                    "Corr": exp.metrics.get("Corr"),
                    "Bias": exp.metrics.get("Bias"),
                    "FHV": exp.metrics.get("FHV"),
                    "FLV": exp.metrics.get("FLV"),
                    "objective_value": exp.objective_value,
                    "rep": exp.rep,
                    "ngs": exp.ngs,
                    "random_seed": exp.random_seed,
                    "model": exp.model_name,
                    "kernel_size": exp.kernel_size,
                    "figure_count": exp.figure_count,
                    "flood_event_count": exp.flood_event_count,
                    "result_dir": rel(exp.result_dir, root),
                    "config_path": rel(exp.config_path, root),
                }
            )


def write_markdown(path: Path, experiments: list[ExperimentResult], basin: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Songliao Experiment Comparison",
        "",
        f"- Basin: `{basin}`",
        f"- Experiments found: {len(experiments)}",
        "",
    ]
    if experiments:
        best = experiments[0]
        lines.extend(
            [
                "## Best Experiment",
                "",
                f"- Experiment: `{best.name}`",
                f"- NSE: `{fmt(best.metrics.get('NSE'))}`",
                f"- KGE: `{fmt(best.metrics.get('KGE'))}`",
                f"- RMSE: `{fmt(best.metrics.get('RMSE'))}`",
                f"- Objective value: `{fmt(best.objective_value)}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Ranking",
            "",
            "| Rank | Experiment | NSE | KGE | RMSE | Corr | Objective | rep | ngs | seed | model | kernel | figures | flood events |",
            "|------|------------|-----|-----|------|------|-----------|-----|-----|------|-------|--------|---------|--------------|",
        ]
    )
    for rank, exp in enumerate(experiments, 1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    f"`{exp.name}`",
                    fmt(exp.metrics.get("NSE")),
                    fmt(exp.metrics.get("KGE")),
                    fmt(exp.metrics.get("RMSE")),
                    fmt(exp.metrics.get("Corr")),
                    fmt(exp.objective_value),
                    fmt(exp.rep, 0),
                    fmt(exp.ngs, 0),
                    fmt(exp.random_seed, 0),
                    exp.model_name or "-",
                    fmt(exp.kernel_size, 0),
                    str(exp.figure_count),
                    str(exp.flood_event_count),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report reads existing outputs only; it does not rerun calibration.",
            "- Use it after each parameter/model trial to keep experiment comparison reproducible.",
            "- The table helps identify whether a new config improves validation NSE and whether figures were generated.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    results_dir = (root / args.results_dir).resolve()
    output_dir = (root / args.output_dir).resolve()

    experiments = collect(root, results_dir, args.basin)
    if not experiments:
        print(f"No evaluated experiments found under {results_dir}")
        return 1

    print(f"Songliao experiment comparison for basin {args.basin}")
    print(f"Results directory: {results_dir}")
    print()
    print_table(experiments)

    if not args.no_write:
        csv_path = output_dir / "songliao_experiment_comparison.csv"
        md_path = output_dir / "songliao_experiment_comparison.md"
        write_csv(csv_path, experiments, root)
        write_markdown(md_path, experiments, args.basin)
        print()
        print(f"Wrote: {csv_path}")
        print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
