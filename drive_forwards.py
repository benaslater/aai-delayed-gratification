"""
Minimal test script that drives the AnimalAI agent forwards until the episode ends.
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

# Discrete action: continuous actions array shape is (1, 2) — [forward/back, left/right]
# Index 1 = move forward
forwards_action = ActionTuple(np.zeros((1, 0), dtype=np.float32), np.array([[1, 0]], dtype=np.int32))
nothing_action  = ActionTuple(np.zeros((1, 0), dtype=np.float32), np.array([[0, 0]], dtype=np.int32))


def run_forwards(config_file: str, exe_path: str) -> float:
    """Drive the agent forwards for an entire episode and return the total reward."""
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

        env.step()
        decision_steps, terminal_steps = env.get_steps(behaviour_name)

        while len(terminal_steps) == 0:
            # Send the forwards action for every agent awaiting a decision
            if len(decision_steps) > 0:
                env.set_actions(behaviour_name, forwards_action)
            env.step()
            decision_steps, terminal_steps = env.get_steps(behaviour_name)

            for step in decision_steps:
                total_reward += decision_steps[step].reward
            for step in terminal_steps:
                total_reward += terminal_steps[step].reward

        if total_reward > 1.5:
            print("PASS: rolling reward (GoodGoalMulti) was collected before the episode ended.")
        else:
            print("FAIL: rolling reward (GoodGoalMulti) was NOT collected.")
        return total_reward

    finally:
        env.close()


if __name__ == "__main__":
    reward = run_forwards(CONFIG_FILE, AAI_EXE_PATH)
    print(f"Done. Reward = {reward:.4f}")
