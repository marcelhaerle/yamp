import os
from enum import IntEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(Exception):
    pass


class AlertPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


class AlertConfig(BaseModel):
    threshold: float
    duration: str = "5m"
    priority: AlertPriority = AlertPriority.NORMAL


class Metric(BaseModel):
    title: str
    query: str
    unit: str = ""
    alert: AlertConfig | None = None


class Dashboard(BaseModel):
    name: str
    refresh_interval: int = Field(default=30, gt=0)
    metrics: list[Metric]


class YampConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YAMP_")

    prometheus_url: HttpUrl
    pushover_token: str
    pushover_user: str
    dashboards: list[Dashboard]


def get_config_path() -> Path:
    """
    Determines the config path from environment variable or default.
    """
    if env_path := os.getenv("YAMP_CONFIG_PATH"):
        return Path(env_path)
    # Default path is relative to the project root
    return Path(__file__).parent.parent.parent / "config" / "yamp.yaml"


def load_config() -> YampConfig:
    """
    Parses the YAML file and validates it against the YampConfig model.
    """
    path = get_config_path()
    if not path.exists():
        raise ConfigError(f"Config file not found at {path}")

    try:
        with path.open("r") as f:
            config_data = yaml.safe_load(f)
        return YampConfig(**config_data)
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML file: {e}") from e
    except ValidationError as e:
        raise ConfigError(f"Configuration validation error: {e}") from e
