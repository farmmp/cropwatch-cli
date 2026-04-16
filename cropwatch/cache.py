"""Simple file-based cache for USDA API responses."""

import json
import time
from pathlib import Path
from typing import Any, Optional

DEFAULT_CACHE_DIR = Path.home() / ".cropwatch" / "cache"
DEFAULT_TTL = 3600  # 1 hour


def _cache_path(key: str, cache_dir: Path) -> Path:
    safe_key = key.replace("/", "_").replace(" ", "_")
    return cache_dir / f"{safe_key}.json"


def get_cached(key: str, ttl: int = DEFAULT_TTL, cache_dir: Path = DEFAULT_CACHE_DIR) -> Optional[Any]:
    """Return cached data for key if present and not expired, else None."""
    path = _cache_path(key, cache_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if time.time() - data["timestamp"] > ttl:
            path.unlink(missing_ok=True)
            return None
        return data["payload"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def set_cached(key: str, payload: Any, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
    """Write payload to cache under key."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key, cache_dir)
    data = {"timestamp": time.time(), "payload": payload}
    try:
        path.write_text(json.dumps(data))
    except OSError:
        pass


def clear_cache(cache_dir: Path = DEFAULT_CACHE_DIR) -> int:
    """Delete all cache files. Returns number of files removed."""
    if not cache_dir.exists():
        return 0
    count = 0
    for f in cache_dir.glob("*.json"):
        try:
            f.unlink()
            count += 1
        except OSError:
            pass
    return count
