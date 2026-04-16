"""
Drives the AnimalAI agent with N no-op steps followed by forwards movement.
For each unique ramp height found in the configs/ folder, runs one representative
config and finds the minimum number of no-ops needed for the rolling reward
(GoodGoalMulti) to reach the agent before the episode-ending goal (GoodGoal)
is collected.

Usage:
    uv run python find_min_wait_time.py           # table output only
    uv run python find_min_wait_time.py --verbose  # show each trial
"""

import argparse
import csv
import os
import sys
import numpy as np
from pathlib import Path
from mlagents_envs.base_env import ActionTuple
from config_utils import get_configs

# Add the local animal-ai-python package to the path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "animal-ai-python"))

from animalai.environment import AnimalAIEnvironment

AAI_EXE_PATH = os.environ["AAI_EXE_PATH"]
CONFIGS_DIR = Path(__file__).parent / "configs"

# This script always tests the specific scenario where the agent must collect
# the rolling reward (GoodGoalMulti) on the ramp before the terminal goal (GoodGoal).
MAIN_TYPE = "goodgoal"
RAMP_GOAL_TYPE = "goodgoalmulti"

forwards_action = ActionTuple(np.zeros((1, 0), dtype=np.float32), np.array([[1, 0]], dtype=np.int32))
nothing_action  = ActionTuple(np.zeros((1, 0), dtype=np.float32), np.array([[0, 0]], dtype=np.int32))


def run_episode(config_file: str, n_noop: int) -> float:
    """Run one episode: n_noop no-op steps then forwards until done.
    Returns total_reward."""
    env = AnimalAIEnvironment(
        file_name=AAI_EXE_PATH,
        arenas_configurations=config_file,
        seed=42,
        useCamera=True,
        useRayCasts=True,
        no_graphics=False,
        inference=True,
    )

    try:
        behaviour_name = list(env.behavior_specs.keys())[0]
        total_reward = 0.0
        steps_taken = 0

        env.step()
        decision_steps, terminal_steps = env.get_steps(behaviour_name)

        while len(terminal_steps) == 0:
            if len(decision_steps) > 0:
                action = nothing_action if steps_taken < n_noop else forwards_action
                env.set_actions(behaviour_name, action)
            env.step()
            steps_taken += 1
            decision_steps, terminal_steps = env.get_steps(behaviour_name)

            for step in decision_steps:
                total_reward += decision_steps[step].reward
            for step in terminal_steps:
                total_reward += terminal_steps[step].reward

        return total_reward

    finally:
        env.close()


def try_noop(config_file: str, n: int, verbose: bool) -> bool:
    reward = run_episode(config_file, n)
    passed = reward > 1.5
    if verbose:
        print(f"  {n} no-op(s): reward={reward:.4f} -> {'PASS' if passed else 'FAIL'}")
    return passed


def find_min_noop(config_file: str, verbose: bool) -> int:
    """Return the minimum passing no-op count."""
    # Phase 1: exponential search to find an upper bound
    if try_noop(config_file, 0, verbose):
        print("====0====")
        return 0
    n = 1
    print("====1====")
    while not try_noop(config_file, n, verbose):
        print(f"===={n}====")
        n *= 2
    hi = n
    lo = n // 2  # last known failure

    # Phase 2: binary search in [lo+1, hi]
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if try_noop(config_file, mid, verbose):
            hi = mid
        else:
            lo = mid

    return hi


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="Print each trial as it runs")
    parser.add_argument("--ramp", type=int, nargs="+", metavar="H",
                        help="Ramp height(s) to include, e.g. --ramp 2 4 6")
    parser.add_argument("--wall", nargs="+", metavar="TYPE",
                        help="Wall goal type(s) to include")
    args = parser.parse_args()
    # get_configs (config_utils.py) reads main and ramp_goal off the args
    # namespace, so set them here as fixed values for this script.
    args.main = [MAIN_TYPE]
    args.ramp_goal = [RAMP_GOAL_TYPE]

    all_configs = get_configs(args)
    if not all_configs:
        print(f"No matching configs found in {CONFIGS_DIR}")
        return

    # One representative config per ramp height is sufficient
    seen_heights = set()
    configs = []
    for config in all_configs:
        height = int(config.stem.split("_")[1])
        if height <= 0:
            continue
        if height not in seen_heights:
            seen_heights.add(height)
            configs.append(config)

    results = []
    for config in configs:
        if args.verbose:
            print(f"\n--- {config.name} ---")
        min_noops = find_min_noop(str(config), args.verbose)
        results.append((config.name, min_noops))

    # Print table
    name_w = max(len(name) for name, _ in results)
    print(f"\n{'Filename':<{name_w}}  Min no-ops")
    print(f"{'-' * name_w}  ----------")
    for name, noops in results:
        print(f"{name:<{name_w}}  {noops}")

    # Write CSV
    csv_path = Path(__file__).parent / "min_wait_times.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "min_noops"])
        writer.writerows(results)
    print(f"\nResults written to {csv_path}")


if __name__ == "__main__":
    main()
