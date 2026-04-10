"""
For each ramp_height_*.yml config in configs/, captures the first camera frame
and saves it as a PNG to frames/.

Usage:
    uv run python capture_first_frames.py
"""

import os
import sys
import numpy as np
from pathlib import Path
from PIL import Image
from mlagents_envs.base_env import ActionTuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "animal-ai-python"))

from animalai.environment import AnimalAIEnvironment

AAI_EXE_PATH = os.environ["AAI_EXE_PATH"]
CONFIGS_DIR = Path(__file__).parent / "configs"
FRAMES_DIR = Path(__file__).parent / "frames"


def capture_first_frame(config_file: str) -> np.ndarray:
    """Launch the environment, take one step, and return the first camera frame as uint8 (H, W, C)."""
    env = AnimalAIEnvironment(
        file_name=AAI_EXE_PATH,
        arenas_configurations=config_file,
        seed=42,
        useCamera=True,
        useRayCasts=False,
        no_graphics=False,
        inference=True,
    )
    try:
        behaviour_name = list(env.behavior_specs.keys())[0]
        env.step()
        decision_steps, _ = env.get_steps(behaviour_name)
        obs = decision_steps.obs[0][0]  # (C, H, W), float32 [0, 1]
        if obs.shape[0] in (1, 3):
            obs = np.transpose(obs, (1, 2, 0))  # -> (H, W, C)
        return (obs * 255).astype(np.uint8)
    finally:
        env.close()


def main():
    configs = sorted(
        CONFIGS_DIR.glob("ramp_height_*.yml"),
        key=lambda p: float(p.stem.removeprefix("ramp_height_")),
    )
    if not configs:
        print(f"No ramp_height_*.yml files found in {CONFIGS_DIR}")
        return

    FRAMES_DIR.mkdir(exist_ok=True)

    for config in configs:
        print(f"Capturing {config.name} ...", end=" ", flush=True)
        frame = capture_first_frame(str(config))
        out_path = FRAMES_DIR / f"{config.stem}.png"
        Image.fromarray(frame).save(out_path)
        print(f"saved {out_path.name}")


if __name__ == "__main__":
    main()
