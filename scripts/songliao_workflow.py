#!/usr/bin/env python3
"""Read-only Songliao entry point matching the command suggested in issue #4.

Only ``doctor`` and ``commands`` are implemented. They inspect the environment
and print copy-paste commands; they never run calibration, evaluation, or
visualization, and they never install packages or write files.

Examples::

    python scripts/songliao_workflow.py doctor
    python scripts/songliao_workflow.py commands
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_env  # noqa: E402

USAGE = """\
usage: python scripts/songliao_workflow.py {doctor,commands} [options]

Read-only helpers:
  doctor     Inspect Python, packages, data paths, scripts, encoding, GPU
  commands   Print calibrate / evaluate / visualize commands (does not run them)

This wrapper does not provide calibrate / evaluate / visualize / compare
subcommands on purpose: those would launch long jobs or write results.
Use the commands printed by ``doctor`` or ``commands``, from hydromodel/.

Extra options are forwarded to scripts/check_env.py (see --help there).
"""


def main(argv: list[str] | None = None) -> int:
    """Dispatch doctor/commands to the read-only check_env script.

    Args:
        argv: Optional argument list without the program name.

    Returns:
        Process exit code from ``check_env.main``.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print(USAGE)
        return 0
    command = args[0]
    rest = args[1:]
    if command == "doctor":
        return check_env.main(rest)
    if command == "commands":
        return check_env.main(["--commands-only", *rest])
    print(
        f"[FAIL] unsupported subcommand: {command}\n"
        "This entry is read-only and only implements doctor / commands.\n"
        "To run calibration, print the commands first:\n"
        "  python scripts/songliao_workflow.py commands",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
