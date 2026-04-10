"""Play the example arena yourself. Press Q in the Unity window to quit."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "animal-ai-python"))

from animalai.play import play

play(
    configuration_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "example_arena.yml"),
    env_path=os.environ["AAI_EXE_PATH"],
)
