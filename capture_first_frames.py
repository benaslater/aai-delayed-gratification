"""
For each ramp_*.yml config in configs/, captures the first N camera frames
and saves them to frames/frame_000/, frames/frame_001/, etc.

Usage:
    uv run python capture_first_frames.py           # 1 frame
    uv run python capture_first_frames.py --n 10    # first 10 frames
"""

import argparse
import os
import sys
import numpy as np
from pathlib import Path
from PIL import Image
from config_utils import add_filter_args, get_configs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "animal-ai-python"))

from animalai.environment import AnimalAIEnvironment

AAI_EXE_PATH = os.environ["AAI_EXE_PATH"]
CONFIGS_DIR = Path(__file__).parent / "configs"
FRAMES_DIR = Path(__file__).parent / "frames"


def capture_frames(config_file: str, n: int) -> list[np.ndarray]:
    """Launch the environment and return the first n camera frames as uint8 (H, W, C)."""
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
        frames = []
        decision_steps, terminal_steps = env.get_steps(behaviour_name)
        for _ in range(n):
            for _ in range(2):  # step twice, capture every other frame
                env.step()
                decision_steps, terminal_steps = env.get_steps(behaviour_name)
                if len(terminal_steps) > 0:
                    break
            obs_batch = terminal_steps.obs[0] if len(terminal_steps) > 0 else decision_steps.obs[0]
            obs = obs_batch[0]  # (C, H, W), float32 [0, 1]
            if obs.shape[0] in (1, 3):
                obs = np.transpose(obs, (1, 2, 0))  # -> (H, W, C)
            frames.append((obs * 255).astype(np.uint8))
            if len(terminal_steps) > 0:
                break
        return frames
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=5, help="Number of frames to capture (default: 5)")
    add_filter_args(parser)
    args = parser.parse_args()

    configs = get_configs(args)
    if not configs:
        print(f"No matching configs found in {CONFIGS_DIR}")
        return

    for config in configs:
        print(f"Capturing {config.name} ...", end=" ", flush=True)
        frames = capture_frames(str(config), args.n)
        config_dir = FRAMES_DIR / config.stem
        config_dir.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(frames):
            Image.fromarray(frame).save(config_dir / f"frame_{i:03d}.png")
        print(f"{len(frames)} frame(s) saved")


if __name__ == "__main__":
    main()
