"""Persistent configuration stored under the user config directory."""

import dataclasses
import json
import os
import pathlib
import typing

APP_NAME = "kuma-status-cli"


class ConfigError(Exception):
    """Raised when the stored configuration is missing or unusable."""


@dataclasses.dataclass(slots=True)
class Config:
    """Uptime Kuma connection settings."""

    url: str
    username: str
    password: str


def config_dir() -> pathlib.Path:
    """Return the directory holding the configuration file."""
    root = os.environ.get("XDG_CONFIG_HOME")
    base = pathlib.Path(root) if root else pathlib.Path.home() / ".config"
    return base / APP_NAME


def config_path() -> pathlib.Path:
    """Return the path of the configuration file."""
    return config_dir() / "config.json"


def load() -> Config:
    """Read the stored configuration, raising ConfigError when unavailable."""
    path = config_path()
    if not path.exists():
        raise ConfigError(f"No configuration found at {path}. Run 'kuma-status-cli configure' first.")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"Could not read {path}: {error}") from error

    if not isinstance(raw, dict):
        raise ConfigError(f"{path} does not contain a JSON object.")
    data = typing.cast(dict[str, typing.Any], raw)

    missing = [key for key in ("url", "username", "password") if not data.get(key)]
    if missing:
        raise ConfigError(f"{path} is missing: {', '.join(missing)}. Run 'kuma-status-cli configure' again.")

    return Config(url=str(data["url"]), username=str(data["username"]), password=str(data["password"]))


def save(config: Config) -> pathlib.Path:
    """Write the configuration with owner-only permissions and return its path."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataclasses.asdict(config), indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def normalize_url(url: str) -> str:
    """Return the URL with a scheme and without a trailing slash."""
    cleaned = url.strip().rstrip("/")
    if not cleaned:
        raise ConfigError("The Uptime Kuma URL must not be empty.")
    if "://" not in cleaned:
        cleaned = f"https://{cleaned}"
    return cleaned
