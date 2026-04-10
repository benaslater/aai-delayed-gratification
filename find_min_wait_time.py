"""
Drives the AnimalAI agent with N no-op steps followed by forwards movement.
Searches for the minimum number of no-ops needed for the rolling reward (GoodGoalMulti)
to reach the agent before the episode-ending goal (GoodGoal) is collected.
Follows the pattern from https://github.com/Kinds-of-Intelligence-CFI/animal-ai-e2e
"""

import os
import sys
import numpy as np
from mlagents_envs.base_env import ActionTuple

# Add the local animal-ai-python package to the path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AAI_PYTHON_PATH = os.path.join(REPO_ROOT, "animal-ai-python")
sys.path.insert(0, AAI_PYTHON_PATH)

from animalai.environment import AnimalAIEnvironment

AAI_EXE_PATH = r"AAI_EXE_PATH_PLACEHOLDER"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_arena.yml")

forwards_action = ActionTuple(np.zeros((1, 0), dtype=np.float32), np.array([[1, 0]], dtype=np.int32))
nothing_action  = ActionTuple(np.zeros((1, 0), dtype=np.float32), np.array([[0, 0]], dtype=np.int32))


def run_episode(config_file: str, exe_path: str, n_noop: int) -> float:
    """Run one episode: n_noop no-op steps then forwards until done. Returns total reward."""
    env = AnimalAIEnvironment(
        file_name=exe_path,
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


def try_noop(config_file: str, exe_path: str, n: int) -> bool:
    print(f"Trying {n} no-op(s)... ", end="", flush=True)
    reward = run_episode(config_file, exe_path, n)
    passed = reward > 1.5
    print(f"reward={reward:.4f} -> {'PASS' if passed else 'FAIL'}")
    return passed


def find_min_noop(config_file: str, exe_path: str) -> None:
    """Search for the minimum number of no-ops for the rolling reward to be collected."""
    # Phase 1: exponential search to find an upper bound
    if try_noop(config_file, exe_path, 0):
        print(f"\nMinimum no-ops needed: 0")
        return
    n = 1
    while not try_noop(config_file, exe_path, n):
        n *= 2
    hi = n
    lo = n // 2  # last known failure

    # Phase 2: binary search in [lo+1, hi]
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if try_noop(config_file, exe_path, mid):
            hi = mid
        else:
            lo = mid

    print(f"\nMinimum no-ops needed: {hi}")


if __name__ == "__main__":
    find_min_noop(CONFIG_FILE, AAI_EXE_PATH)
