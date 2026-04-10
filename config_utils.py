"""Shared config discovery and filtering for find_min_wait_time and capture_first_frames."""

import argparse
from pathlib import Path

CONFIGS_DIR = Path(__file__).parent / "configs"
GOAL_TYPES = ["goodgoal", "goodgoalmulti", "absent"]


def add_filter_args(parser: argparse.ArgumentParser) -> None:
    """Add per-dimension filter flags to an argparse parser."""
    parser.add_argument("--ramp", type=int, nargs="+", metavar="H",
                        help="Ramp height(s) to include, e.g. --ramp 2 4 6")
    parser.add_argument("--main", nargs="+", choices=GOAL_TYPES, metavar="TYPE",
                        help="Main goal type(s) to include")
    parser.add_argument("--ramp-goal", nargs="+", choices=GOAL_TYPES, metavar="TYPE",
                        help="Ramp goal type(s) to include")
    parser.add_argument("--wall", nargs="+", choices=GOAL_TYPES, metavar="TYPE",
                        help="Wall goal type(s) to include")


def get_configs(args: argparse.Namespace) -> list[Path]:
    """Return configs matching the filter args, sorted by ramp height."""
    configs = []
    for p in CONFIGS_DIR.glob("ramp_*.yml"):
        parts = p.stem.split("_")
        # Expected: ramp {h} main {main} ramp {ramp} wall {wall}
        if len(parts) != 8:
            continue
        height = int(parts[1])
        main_type = parts[3]
        ramp_type = parts[5]
        wall_type = parts[7]

        if args.ramp and height not in args.ramp:
            continue
        if args.main and main_type not in args.main:
            continue
        if args.ramp_goal and ramp_type not in args.ramp_goal:
            continue
        if args.wall and wall_type not in args.wall:
            continue

        configs.append(p)

    return sorted(configs, key=lambda p: int(p.stem.split("_")[1]))
