from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import ConfigError, get_config_path, load_config


def test_get_config_path_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure default path is correct when no env var is set."""
    monkeypatch.delenv("YAMP_CONFIG_PATH", raising=False)
    # This relies on the test being run from the project root
    expected_path = Path.cwd() / "config" / "yamp.yaml"
    assert get_config_path() == expected_path


def test_get_config_path_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure env var override works."""
    monkeypatch.setenv("YAMP_CONFIG_PATH", "/tmp/custom.yaml")
    assert get_config_path() == Path("/tmp/custom.yaml")


def test_load_config_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading a valid YAML file with secrets from env."""
    config_file = tmp_path / "yamp.yaml"
    content = """
prometheus_url: "http://localhost:9090"
dashboards:
  - name: "Test Dash"
    metrics:
      - title: "CPU"
        query: "node_cpu"
    """
    config_file.write_text(content)

    monkeypatch.setenv("YAMP_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("YAMP_PUSHOVER_TOKEN", "token123")
    monkeypatch.setenv("YAMP_PUSHOVER_USER", "user456")

    config = load_config()
    assert config.prometheus_url.unicode_string() == "http://localhost:9090/"
    assert config.pushover_token == "token123"
    assert config.pushover_user == "user456"
    assert len(config.dashboards) == 1
    assert config.dashboards[0].name == "Test Dash"


def test_load_config_file_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a ConfigError is raised for a missing file."""
    monkeypatch.setenv("YAMP_CONFIG_PATH", "/tmp/non_existent_file.yaml")
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config()


def test_load_config_malformed_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a ConfigError is raised for a malformed YAML."""
    config_file = tmp_path / "bad_yamp.yaml"
    config_file.write_text("prometheus_url: http://localhost:9090\n- dashboard:")
    monkeypatch.setenv("YAMP_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("YAMP_PUSHOVER_TOKEN", "token123")
    monkeypatch.setenv("YAMP_PUSHOVER_USER", "user456")

    with pytest.raises(ConfigError, match="Error parsing YAML file"):
        load_config()


def test_load_config_validation_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a ConfigError is raised for invalid data."""
    config_file = tmp_path / "invalid_yamp.yaml"
    # Missing required 'prometheus_url'
    content = """
dashboards:
  - name: "Bad Dash"
    metrics: []
    """
    config_file.write_text(content)
    monkeypatch.setenv("YAMP_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("YAMP_PUSHOVER_TOKEN", "token123")
    monkeypatch.setenv("YAMP_PUSHOVER_USER", "user456")

    with pytest.raises(ConfigError, match="Configuration validation error"):
        load_config()


def test_load_config_missing_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that validation fails if secrets are not in the environment."""
    config_file = tmp_path / "yamp.yaml"
    content = """
prometheus_url: "http://localhost:9090"
dashboards: []
    """
    config_file.write_text(content)
    monkeypatch.setenv("YAMP_CONFIG_PATH", str(config_file))

    # YAMP_PUSHOVER_TOKEN and YAMP_PUSHOVER_USER are not set
    monkeypatch.delenv("YAMP_PUSHOVER_TOKEN", raising=False)
    monkeypatch.delenv("YAMP_PUSHOVER_USER", raising=False)

    with pytest.raises(ConfigError) as exc_info:
        load_config()

    # We expect the ConfigError to wrap a Pydantic ValidationError
    assert isinstance(exc_info.value.__cause__, ValidationError)
    assert "pushover_token" in str(exc_info.value)
