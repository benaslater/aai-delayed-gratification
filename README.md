# AAI delayed gratification task instance generation

Generate Animal-AI arena configs and find the minimum agent wait time for each.

## Setup

Set `AAI_EXE_PATH` to the Animal-AI executable.

## Scripts

**`generate_configs.py`** — populate `configs/` with arenas varying ramp height.
```
uv run python generate_configs.py --min 2 --max 10 --step 2
```

**`find_min_wait_time.py`** — for each config, find the minimum no-op steps before the agent can collect the rolling reward.
```
uv run python find_min_wait_time.py
```

**`play.py`** — play the example arena manually.
```
uv run python play.py
```
