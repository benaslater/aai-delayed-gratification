"""
Generate arena config YAML files as the cross product of:
  - ramp heights
  - main goal type  (GoodGoal | GoodGoalMulti | absent)
  - ramp goal type  (GoodGoal | GoodGoalMulti | absent)
  - wall goal type  (GoodGoal | GoodGoalMulti | absent)

Ramp geometry is kept consistent across heights:
  - Ramp size y   = abs(ramp_height)
  - Ramp goal y   = ramp_base_y + abs(ramp_height)  (sits on top of ramp)
  - Wall goal y   = 12.0 (one unit above the fixed red wall top at y=11)
  - Red wall size y = 11.0 (fixed)

Special cases:
  - height == 0 : flat — Ramp item is omitted entirely; ramp goal (if any) sits at floor level (y=1.0)
  - height < 0  : ramp slopes the other way — Ramp rotation is 270 (vs. 90 for positive heights)
                  and the ramp goal is placed at the opposite end (x=18.0 instead of x=9.0)

Output files: configs/ramp_{h}_main_{main_type}_ramp_{ramp_type}_wall_{wall_type}.yml

Usage:
    uv run python generate_configs.py
    uv run python generate_configs.py --min -10 --max 10 --step 2
"""

import argparse
from itertools import product
from pathlib import Path

CONFIGS_DIR = Path(__file__).parent / "configs"
RAMP_BASE_Y = 1.0
WALL_GOAL_Y = 12.0

GOAL_TYPES = ["GoodGoal", "GoodGoalMulti", "absent"]

GOAL_COLORS = {
    "GoodGoal":      "{r: 0, g: 256, b: 0}",
    "GoodGoalMulti": "{r: 255, g: 255, b: 0}",
}


def goal_item(name: str, x: float, y: float, z: float) -> str:
    return f"""\
    - !Item
      name: {name}
      positions:
      - !Vector3 {{x: {x:.1f}, y: {y:.1f}, z: {z:.1f}}}
      rotations:
      - 0
      sizes:
      - !Vector3 {{x: 1.0, y: 1.0, z: 1.0}}
      colors:
      - !RGB {GOAL_COLORS[name]}"""


def make_arena(ramp_height: float, main_type: str, ramp_type: str, wall_type: str) -> str:
    abs_height = abs(ramp_height)

    if ramp_height == 0:
        # Flat: no ramp; goal (if any) sits at floor level
        ramp_goal_y = RAMP_BASE_Y
        ramp_goal_x = 9.0
        ramp_rotation = 90
    elif ramp_height > 0:
        ramp_goal_y = RAMP_BASE_Y + ramp_height
        ramp_goal_x = 9.0
        ramp_rotation = 90
    else:
        # Negative: ramp slopes the other way; goal moves to the opposite end
        ramp_goal_y = RAMP_BASE_Y + abs_height
        ramp_goal_x = 18.0
        ramp_rotation = 270

    main_item = "" if main_type == "absent" else goal_item(main_type, 20.0, 0.0, 25.0) + "\n"
    ramp_item = "" if ramp_type == "absent" else goal_item(ramp_type, ramp_goal_x, ramp_goal_y, 15.0) + "\n"
    wall_item = "" if wall_type == "absent" else goal_item(wall_type, 15, 0, 11) + "\n"

    ramp_section = "" if ramp_height == 0 else f"""\
    - !Item
      name: Ramp
      positions:
      - !Vector3 {{x: 13.5, y: {RAMP_BASE_Y:.1f}, z: 15.0}}
      rotations:
      - {ramp_rotation}
      sizes:
      - !Vector3 {{x: 1.0, y: {abs_height:.1f}, z: 10.0}}
      colors:
      - !RGB {{r: 165, g: 148, b: 255}}
"""

    return f"""\
!ArenaConfig
arenas:
  0: !Arena
    pass_mark: 0
    t: 0
    items:
{main_item}\
    - !Item
      name: Agent
      positions:
      - !Vector3 {{x: 20.0, y: 1.0, z: 5.0}}
      rotations:
      - 0
      sizes:
      - !Vector3 {{x: 1, y: 1, z: 1}}
      colors:
      - !RGB {{r: 0, g: 0, b: 0}}
    - !Item
      name: Wall
      positions:
      - !Vector3 {{x: 20.0, y: 0.0, z: 5.0}}
      - !Vector3 {{x: 19.0, y: 0.0, z: 20.0}}
      - !Vector3 {{x: 21.0, y: 0.0, z: 20.0}}
      - !Vector3 {{x: 13.5, y: 0.0, z: 15.0}}
      - !Vector3 {{x: 13.5, y: 0.0, z: 16.0}}
      rotations:
      - 0
      - 0
      - 0
      - 0
      - 0
      sizes:
      - !Vector3 {{x: 1.0, y: 1.0, z: 1.0}}
      - !Vector3 {{x: 1.0, y: 1.0, z: 39.0}}
      - !Vector3 {{x: 1.0, y: 2.0, z: 39.0}}
      - !Vector3 {{x: 10.0, y: 1.0, z: 1.0}}
      - !Vector3 {{x: 10.0, y: 11.0, z: 1.0}}
      colors:
      - !RGB {{r: 255, g: 0, b: 255}}
      - !RGB {{r: 255, g: 0, b: 255}}
      - !RGB {{r: 255, g: 0, b: 255}}
      - !RGB {{r: 255, g: 0, b: 255}}
      - !RGB {{r: 255, g: 0, b: 0}}
{ramp_section}\
{ramp_item}\
{wall_item}"""


def type_slug(t: str) -> str:
    return t.lower().replace("goodgoal", "good_goal").replace("goodgoalmulti", "good_goalmulti") if t != "absent" else "absent"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--min", type=float, default=-10.0, dest="min_h", help="Minimum ramp height, may be negative (default: -10)")
    parser.add_argument("--max", type=float, default=10.0, dest="max_h", help="Maximum ramp height (default: 10)")
    parser.add_argument("--step", type=float, default=2.0, help="Step size between heights (default: 2)")
    args = parser.parse_args()

    CONFIGS_DIR.mkdir(exist_ok=True)

    heights = []
    h = args.min_h
    while h <= args.max_h + 1e-9:
        heights.append(h)
        h += args.step

    slugs = {t: t.lower() for t in GOAL_TYPES}

    combos = list(product(heights, GOAL_TYPES, GOAL_TYPES, GOAL_TYPES))
    print(f"Generating {len(combos)} config(s) in {CONFIGS_DIR}/")

    for h, main_type, ramp_type, wall_type in combos:
        filename = CONFIGS_DIR / f"ramp_{h:.0f}_main_{slugs[main_type]}_ramp_{slugs[ramp_type]}_wall_{slugs[wall_type]}.yml"
        filename.write_text(make_arena(h, main_type, ramp_type, wall_type))
        print(f"  wrote {filename.name}")


if __name__ == "__main__":
    main()
