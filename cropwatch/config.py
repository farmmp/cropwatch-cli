"""Configuration helpers for cropwatch-cli."""
import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "cropwatch"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "api_key": None,
    "default_state": None,
    "default_year": None,
    "bar_width": 30,
}


def load_config() -> dict:
    """Load config from disk, falling back to defaults."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        with CONFIG_FILE.open() as f:
            data = json.load(f)
        config = dict(DEFAULTS)
        config.update({k: v for k, v in data.items() if k in DEFAULTS})
        return config
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save_config(config: dict) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w") as f:
        json.dump(config, f, indent=2)


def get_api_key() -> str | None:
    """Return API key from env var or config file."""
    return os.environ.get("USDA_API_KEY") or load_config().get("api_key")
