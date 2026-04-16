import json
import pytest
from unittest.mock import patch
from pathlib import Path
import cropwatch.config as cfg


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / "config.json")
    yield tmp_path


def test_load_config_defaults(tmp_config):
    config = cfg.load_config()
    assert config["api_key"] is None
    assert config["bar_width"] == 30


def test_save_and_load_config(tmp_config):
    cfg.save_config({"api_key": "mykey", "default_state": "IA", "default_year": 2022, "bar_width": 20})
    config = cfg.load_config()
    assert config["api_key"] == "mykey"
    assert config["default_state"] == "IA"
    assert config["bar_width"] == 20


def test_load_config_ignores_unknown_keys(tmp_config):
    (tmp_config / "config.json").write_text(json.dumps({"api_key": "x", "unknown": "y"}))
    config = cfg.load_config()
    assert "unknown" not in config
    assert config["api_key"] == "x"


def test_load_config_bad_json(tmp_config):
    (tmp_config / "config.json").write_text("not json")
    config = cfg.load_config()
    assert config == dict(cfg.DEFAULTS)


def test_get_api_key_env_takes_priority(tmp_config, monkeypatch):
    cfg.save_config({"api_key": "filekey", "default_state": None, "default_year": None, "bar_width": 30})
    monkeypatch.setenv("USDA_API_KEY", "envkey")
    assert cfg.get_api_key() == "envkey"


def test_get_api_key_falls_back_to_file(tmp_config, monkeypatch):
    monkeypatch.delenv("USDA_API_KEY", raising=False)
    cfg.save_config({"api_key": "filekey", "default_state": None, "default_year": None, "bar_width": 30})
    assert cfg.get_api_key() == "filekey"
