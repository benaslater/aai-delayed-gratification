"""Parse Animal-AI task run-result JSON files into tidy DataFrames.

Designed to be reused across notebooks for any task whose trial ids follow the
shared `trial_ramp_<H>_main_<TYPE>_ramp_<TYPE>_wall_<TYPE>-<hash>` convention
used by the configs in ./configs.
"""

import json
import re
from pathlib import Path

import pandas as pd

TRIAL_ID_RE = re.compile(
    r"^trial_ramp_(-?\d+)_main_(\w+?)_ramp_(\w+?)_wall_(\w+?)-[0-9a-f]+$"
)


def parse_trial_id(trial_id: str) -> dict | None:
    """Extract ramp height and goal types from a trial id, or None if it doesn't match."""
    match = TRIAL_ID_RE.match(trial_id)
    if match is None:
        return None
    height, main, ramp_goal, wall = match.groups()
    return {
        "ramp_height": int(height),
        "main": main,
        "ramp_goal": ramp_goal,
        "wall": wall,
    }


def _trial_conversation(subrun: dict) -> dict | None:
    for conv in subrun.get("conversations", []):
        if str(conv.get("id", "")).startswith("trial_"):
            return conv
    return None


def _assistant_text(conversation: dict) -> str | None:
    for request in conversation.get("requests", []):
        for content in request.get("contents", []):
            if content.get("role") != "CONTENT_ROLE_ASSISTANT":
                continue
            for part in content.get("parts", []):
                text = part.get("text")
                if text is not None:
                    return text
    return None


def load_run(path: str | Path) -> pd.DataFrame:
    """Parse one ``*.run.json`` file into one row per trial.

    Columns: ramp_height, main, ramp_goal, wall, correct, response,
    input_tokens, output_tokens, latency_ms, model, run_file, trial_id.
    """
    path = Path(path)
    with path.open() as f:
        data = json.load(f)

    model = data.get("modelVersion", {}).get("slug")
    rows = []

    for subrun in data.get("subruns", []):
        conversation = _trial_conversation(subrun)
        if conversation is None:
            continue
        parsed = parse_trial_id(conversation["id"])
        if parsed is None:
            continue

        results = subrun.get("results") or [{}]
        correct = float(results[0].get("numericResult", {}).get("value", 0.0))

        metrics = conversation.get("metrics", {})
        latency = metrics.get("totalBackendLatencyMs")

        n_goals = sum(parsed[k] != "absent" for k in ("main", "ramp_goal", "wall"))

        rows.append({
            **parsed,
            "n_goals": n_goals,
            "correct": correct,
            "response": _assistant_text(conversation),
            "input_tokens": metrics.get("inputTokens"),
            "output_tokens": metrics.get("outputTokens"),
            "latency_ms": int(latency) if latency is not None else None,
            "model": model,
            "run_file": path.name,
            "trial_id": conversation["id"],
        })

    return pd.DataFrame(rows)


def overall_accuracy(df: pd.DataFrame) -> float:
    """Mean of the per-trial ``correct`` column."""
    return float(df["correct"].mean())


def accuracy_by(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Accuracy and trial count grouped by an arbitrary column, sorted by that column."""
    grouped = df.groupby(column)["correct"].agg(["mean", "size"])
    return grouped.rename(columns={"mean": "accuracy", "size": "n_trials"}).reset_index()


def accuracy_by_ramp(df: pd.DataFrame) -> pd.DataFrame:
    """Accuracy and trial count grouped by ramp_height, sorted by ramp_height."""
    return accuracy_by(df, "ramp_height")


def accuracy_by_n_goals(df: pd.DataFrame) -> pd.DataFrame:
    """Accuracy and trial count grouped by n_goals (0-3), sorted by n_goals."""
    return accuracy_by(df, "n_goals")
