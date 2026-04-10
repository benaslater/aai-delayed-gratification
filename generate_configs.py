"""
Generate arena config YAML files by systematically varying the ramp height.

For each height, the GoodGoalMulti position and the blocking wall height are
adjusted to remain consistent with the ramp geometry:
  - Ramp size y         = ramp_height
  - GoodGoalMulti y     = ramp_base_y + ramp_height  (sits on top of ramp)
  - Red wall size y     = ramp_base_y + ramp_height  (matches ramp top)

Output files are written to configs/ramp_height_<h>.yml.

Usage:
    uv run python generate_configs.py
    uv run python generate_configs.py --min 2 --max 20 --step 2
"""

import argparse
from pathlib import Path

CONFIGS_DIR = Path(__file__).parent / "configs"

# Ramp base position (y stays fixed; only the size varies)
RAMP_BASE_Y = 1.0


def make_arena(ramp_height: float) -> str:
    goal_multi_y = RAMP_BASE_Y + ramp_height

    return f"""\
!ArenaConfig
arenas:
  0: !Arena
    pass_mark: 0
    t: 0
    items:
    - !Item
      name: GoodGoal
      positions:
      - !Vector3 {{x: 20.0, y: 0.0, z: 25.0}}
      rotations:
      - 0
      sizes:
      - !Vector3 {{x: 1.0, y: 1.0, z: 1.0}}
      colors:
      - !RGB {{r: 0, g: 256, b: 0}}
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
    - !Item
      name: Ramp
      positions:
      - !Vector3 {{x: 13.5, y: {RAMP_BASE_Y:.1f}, z: 15.0}}
      rotations:
      - 90
      sizes:
      - !Vector3 {{x: 1.0, y: {ramp_height:.1f}, z: 10.0}}
      colors:
      - !RGB {{r: 165, g: 148, b: 255}}
    - !Item
      name: GoodGoalMulti
      positions:
      - !Vector3 {{x: 9.0, y: {goal_multi_y:.1f}, z: 15.0}}
      rotations:
      - 0
      sizes:
      - !Vector3 {{x: 1.0, y: 1.0, z: 1.0}}
      colors:
      - !RGB {{r: 255, g: 255, b: 0}}
"""


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--min", type=float, default=2.0, dest="min_h", help="Minimum ramp height (default: 2)")
    parser.add_argument("--max", type=float, default=10.0, dest="max_h", help="Maximum ramp height (default: 10)")
    parser.add_argument("--step", type=float, default=2.0, help="Step size between heights (default: 2)")
    args = parser.parse_args()

    CONFIGS_DIR.mkdir(exist_ok=True)

    heights = []
    h = args.min_h
    while h <= args.max_h + 1e-9:
        heights.append(h)
        h += args.step

    print(f"Generating {len(heights)} config(s) in {CONFIGS_DIR}/")
    for h in heights:
        filename = CONFIGS_DIR / f"ramp_height_{h:.0f}.yml"
        filename.write_text(make_arena(h))
        print(f"  wrote {filename.name}")


if __name__ == "__main__":
    main()
