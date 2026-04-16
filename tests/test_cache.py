"""Tests for cropwatch.cache module."""

import json
import time
from pathlib import Path

import pytest

from cropwatch.cache import clear_cache, get_cached, set_cached


@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / "cache"


def test_get_cached_missing_returns_none(cache_dir):
    assert get_cached("nonexistent", cache_dir=cache_dir) is None


def test_set_and_get_cached(cache_dir):
    set_cached("test_key", {"data": [1, 2, 3]}, cache_dir=cache_dir)
    result = get_cached("test_key", cache_dir=cache_dir)
    assert result == {"data": [1, 2, 3]}


def test_get_cached_expired(cache_dir):
    set_cached("old_key", "stale", cache_dir=cache_dir)
    # Manually backdate the timestamp
    from cropwatch.cache import _cache_path
    path = _cache_path("old_key", cache_dir)
    data = json.loads(path.read_text())
    data["timestamp"] = time.time() - 7200
    path.write_text(json.dumps(data))

    assert get_cached("old_key", ttl=3600, cache_dir=cache_dir) is None
    assert not path.exists()


def test_get_cached_not_expired(cache_dir):
    set_cached("fresh_key", "fresh", cache_dir=cache_dir)
    assert get_cached("fresh_key", ttl=3600, cache_dir=cache_dir) == "fresh"


def test_get_cached_corrupt_file(cache_dir):
    cache_dir.mkdir(parents=True)
    bad = cache_dir / "bad_key.json"
    bad.write_text("not json{{{")
    assert get_cached("bad_key", cache_dir=cache_dir) is None


def test_clear_cache(cache_dir):
    set_cached("a", 1, cache_dir=cache_dir)
    set_cached("b", 2, cache_dir=cache_dir)
    removed = clear_cache(cache_dir=cache_dir)
    assert removed == 2
    assert get_cached("a", cache_dir=cache_dir) is None


def test_clear_cache_nonexistent_dir(tmp_path):
    missing = tmp_path / "no_such_dir"
    assert clear_cache(cache_dir=missing) == 0
