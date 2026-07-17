from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_BASIN = "songliao_21401550"
DEFAULT_EXPERIMENT = "songliao_event_3h"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def hydromodel_dir(root: Path) -> Path:
    return root / "hydromodel"


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def run_command(cmd: list[str], cwd: Path, env: dict[str, str], dry_run: bool = False) -> int:
    print("Working directory:")
    print(f"  {cwd}")
    print("Command:")
    print("  " + " ".join(cmd))
    print()
    if dry_run:
        return 0
    return subprocess.run(cmd, cwd=str(cwd), env=env, check=False).returncode


def workflow_env(root: Path, use_workspace_cache: bool = False, matplotlib: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if matplotlib:
        env.setdefault("MPLBACKEND", "Agg")
    if use_workspace_cache:
        cache_home = root / ".hydro-workspace"
        env["USERPROFILE"] = str(cache_home)
        env["HOME"] = str(cache_home)
    return env


def import_check(module: str) -> tuple[bool, str]:
    code = f"import {module}; print(getattr({module}, '__file__', 'built-in'))"
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )
    if proc.returncode == 0:
        return True, proc.stdout.strip()
    return False, proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "unknown error"


def cmd_doctor(args: argparse.Namespace) -> int:
    root = repo_root()
    hydro = hydromodel_dir(root)
    print("Songliao workflow doctor")
    print("=" * 72)
    print(f"Repository root : {root}")
    print(f"Hydromodel dir  : {hydro}")
    print(f"Python          : {sys.executable}")
    print(f"Python version  : {sys.version.split()[0]}")
    print()

    ok = True
    required_paths = [
        root / "data" / "songliaorrevent" / "songliaorrevent",
        hydro / "scripts" / "run_event_calibration.py",
        hydro / "scripts" / "run_xaj_evaluate.py",
        hydro / "scripts" / "visualize.py",
        hydro / "configs" / f"{args.experiment}.yaml",
    ]
    for path in required_paths:
        exists = path.exists()
        ok &= exists
        print(f"{'[OK]' if exists else '[FAIL]'} {rel(path, root)}")
    print()

    for module in ["hydromodel", "hydrodatasource", "hydrodataset", "hydroutils"]:
        success, detail = import_check(module)
        ok &= success
        print(f"{'[OK]' if success else '[FAIL]'} import {module}: {detail}")
    print()

    if ok:
        print("[OK] Environment looks ready for Songliao workflow commands.")
        return 0
    print("[FAIL] Environment is incomplete. Check the Python interpreter and local editable installs.")
    print("Hint: use the hydro_homework conda environment, not a random PyCharm virtualenv.")
    return 1


def cmd_calibrate(args: argparse.Namespace) -> int:
    root = repo_root()
    hydro = hydromodel_dir(root)
    config = args.config or f"configs/{args.experiment}.yaml"
    env = workflow_env(root, args.workspace_cache)
    return run_command(
        [sys.executable, "scripts/run_event_calibration.py", "--config", config],
        hydro,
        env,
        args.dry_run,
    )


def cmd_evaluate(args: argparse.Namespace) -> int:
    root = repo_root()
    hydro = hydromodel_dir(root)
    calibration_dir = f"results/songliao_event/{args.experiment}"
    env = workflow_env(root, args.workspace_cache)
    return run_command(
        [
            sys.executable,
            "scripts/run_xaj_evaluate.py",
            "--calibration-dir",
            calibration_dir,
            "--eval-period",
            args.eval_period,
        ],
        hydro,
        env,
        args.dry_run,
    )


def cmd_visualize(args: argparse.Namespace) -> int:
    root = repo_root()
    hydro = hydromodel_dir(root)
    eval_dir = f"results/songliao_event/{args.experiment}/evaluation_test"
    env = workflow_env(root, args.workspace_cache, matplotlib=True)
    return run_command(
        [
            sys.executable,
            "scripts/visualize.py",
            "--eval-dir",
            eval_dir,
            "--basins",
            args.basin,
            "--plot-types",
            *args.plot_types,
        ],
        hydro,
        env,
        args.dry_run,
    )


def cmd_compare(args: argparse.Namespace) -> int:
    root = repo_root()
    env = workflow_env(root, args.workspace_cache)
    return run_command(
        [sys.executable, "scripts/compare_songliao_experiments.py", "--basin", args.basin],
        root,
        env,
        args.dry_run,
    )


def cmd_commands(args: argparse.Namespace) -> int:
    root = repo_root()
    hydro = hydromodel_dir(root)
    print("Equivalent commands")
    print("=" * 72)
    print("From repository root:")
    if os.name == "nt":
        print(f'  cmd / Anaconda Prompt: cd /d "{root}"')
        print(f"  PowerShell: Set-Location -LiteralPath '{root}'")
    else:
        print(f'  cd "{root}"')
    print("  conda activate hydro_homework")
    print()
    print("Doctor:")
    print(f"  python scripts/songliao_workflow.py doctor --experiment {args.experiment}")
    print()
    print("Calibration, evaluation, visualization:")
    if os.name == "nt":
        print(f'  cmd / Anaconda Prompt: cd /d "{hydro}"')
        print(f"  PowerShell: Set-Location -LiteralPath '{hydro}'")
    else:
        print(f'  cd "{hydro}"')
    print(f"  python scripts/run_event_calibration.py --config configs/{args.experiment}.yaml")
    print(
        "  python scripts/run_xaj_evaluate.py "
        f"--calibration-dir results/songliao_event/{args.experiment} --eval-period test"
    )
    print(
        "  python scripts/visualize.py "
        f"--eval-dir results/songliao_event/{args.experiment}/evaluation_test "
        f"--basins {args.basin} --plot-types all"
    )
    print()
    print("Workflow wrapper equivalents:")
    print(f"  python scripts/songliao_workflow.py calibrate --experiment {args.experiment}")
    print(f"  python scripts/songliao_workflow.py evaluate --experiment {args.experiment}")
    print(f"  python scripts/songliao_workflow.py visualize --experiment {args.experiment} --basin {args.basin}")
    print(f"  python scripts/songliao_workflow.py compare --basin {args.basin}")
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace-cache", action="store_true", help="Redirect USERPROFILE cache to repo root.")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running it.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stable one-command entrypoint for Songliao calibration/evaluation workflow."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check paths and Python imports.")
    doctor.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    doctor.set_defaults(func=cmd_doctor)

    calibrate = sub.add_parser("calibrate", help="Run calibration from repo root safely.")
    calibrate.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    calibrate.add_argument("--config", help="Config path relative to hydromodel directory.")
    add_common(calibrate)
    calibrate.set_defaults(func=cmd_calibrate)

    evaluate = sub.add_parser("evaluate", help="Run evaluation from repo root safely.")
    evaluate.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    evaluate.add_argument("--eval-period", default="test")
    add_common(evaluate)
    evaluate.set_defaults(func=cmd_evaluate)

    visualize = sub.add_parser("visualize", help="Generate figures from repo root safely.")
    visualize.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    visualize.add_argument("--basin", default=DEFAULT_BASIN)
    visualize.add_argument("--plot-types", nargs="+", default=["all"])
    add_common(visualize)
    visualize.set_defaults(func=cmd_visualize)

    compare = sub.add_parser("compare", help="Compare existing experiments.")
    compare.add_argument("--basin", default=DEFAULT_BASIN)
    add_common(compare)
    compare.set_defaults(func=cmd_compare)

    commands = sub.add_parser("commands", help="Print equivalent raw commands.")
    commands.add_argument("--experiment", default=DEFAULT_EXPERIMENT)
    commands.add_argument("--basin", default=DEFAULT_BASIN)
    commands.set_defaults(func=cmd_commands)
    return parser


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except AttributeError:
            pass
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
