"""Configuration loader utilities."""

import json
import os
from typing import Any, Dict

from .settings import (
    ConfigurationError,
    Settings,
)


def load_from_file(file_path: str) -> Settings:
    """
    Load configuration from a JSON file.

    Args:
        file_path: Path to configuration file

    Returns:
        Settings object

    Raises:
        ConfigurationError: If file cannot be loaded or is invalid
    """
    if not os.path.exists(file_path):
        raise ConfigurationError(f"Configuration file not found: {file_path}")

    try:
        with open(file_path, "r") as f:
            config_dict = json.load(f)
        return Settings(**config_dict)
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in configuration file: {str(e)}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e


def load_from_env() -> Settings:
    """
    Load configuration from environment variables.

    Returns:
        Settings object

    Raises:
        ConfigurationError: If environment variables are invalid
    """
    try:
        # Load .env file if it exists
        env_file = ".env"
        if os.path.exists(env_file):
            from dotenv import load_dotenv
            load_dotenv(env_file)

        return Settings()
    except Exception as e:
        raise ConfigurationError(f"Failed to load from environment: {str(e)}") from e


def load_from_dict(config_dict: Dict[str, Any]) -> Settings:
    """
    Load configuration from a dictionary.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Settings object

    Raises:
        ConfigurationError: If dictionary is invalid
    """
    try:
        return Settings(**config_dict)
    except Exception as e:
        raise ConfigurationError(f"Failed to load from dictionary: {str(e)}") from e


def create_default_config_file(output_path: str) -> None:
    """
    Create a default configuration file.

    Args:
        output_path: Path to save configuration file

    Raises:
        ConfigurationError: If file cannot be created
    """
    try:
        default_settings = Settings()
        config_dict = default_settings.model_dump()

        # Remove API keys from default config
        if "api" in config_dict:
            config_dict["api"]["openai_api_key"] = None
            config_dict["api"]["anthropic_api_key"] = None

        with open(output_path, "w") as f:
            json.dump(config_dict, f, indent=2)

    except Exception as e:
        raise ConfigurationError(f"Failed to create default config: {str(e)}") from e


def merge_configs(base: Settings, overrides: Dict[str, Any]) -> Settings:
    """
    Merge configuration overrides with base settings.

    Args:
        base: Base settings
        overrides: Configuration overrides

    Returns:
        New Settings object with overrides applied

    Raises:
        ConfigurationError: If merge fails
    """
    try:
        base_dict = base.model_dump()
        _deep_merge(base_dict, overrides)
        return Settings(**base_dict)
    except Exception as e:
        raise ConfigurationError(f"Failed to merge configurations: {str(e)}") from e


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
    """
    Recursively merge nested dictionaries.

    Args:
        base: Base dictionary to update
        updates: Updates to apply
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def validate_config_file(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate a configuration file without loading it.

    Args:
        file_path: Path to configuration file

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if not os.path.exists(file_path):
        errors.append(f"Configuration file not found: {file_path}")
        return False, errors

    try:
        with open(file_path, "r") as f:
            config_dict = json.load(f)

        # Try to create Settings object to validate
        Settings(**config_dict)
        return True, []

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors
