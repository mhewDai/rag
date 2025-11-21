"""Configuration settings for the Property Data Extraction System."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from enum import Enum


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OCRConfig(BaseModel):
    """Configuration for OCR processing."""

    tesseract_cmd: str = Field(
        default="/usr/local/bin/tesseract",
        description="Path to Tesseract executable",
    )
    language: str = Field(default="eng", description="OCR language code")
    dpi: int = Field(default=300, ge=72, le=600, description="DPI for image processing")
    preprocess: bool = Field(default=True, description="Enable image preprocessing")
    denoise: bool = Field(default=True, description="Enable denoising")
    deskew: bool = Field(default=True, description="Enable deskewing")
    contrast_enhancement: bool = Field(default=True, description="Enable contrast enhancement")

    @field_validator("dpi")
    @classmethod
    def validate_dpi(cls, v: int) -> int:
        """Validate DPI is within reasonable range."""
        if v < 72 or v > 600:
            raise ValueError("DPI must be between 72 and 600")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code is not empty."""
        if not v or not v.strip():
            raise ValueError("Language code cannot be empty")
        return v.strip()


class ChunkConfig(BaseModel):
    """Configuration for document chunking."""

    chunk_size: int = Field(default=800, ge=100, le=2000, description="Maximum chunk size in tokens")
    chunk_overlap: int = Field(default=100, ge=0, le=500, description="Overlap between chunks in tokens")
    strategy: str = Field(default="sentence-aware", description="Chunking strategy")
    min_chunk_size: int = Field(default=50, ge=10, description="Minimum chunk size in tokens")

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkConfig":
        """Validate overlap is less than chunk size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        if self.min_chunk_size > self.chunk_size:
            raise ValueError("Minimum chunk size must be less than or equal to chunk size")
        return self


class RAGConfig(BaseModel):
    """Configuration for RAG extraction."""

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name",
    )
    llm_model: str = Field(default="gpt-4", description="LLM model name")
    llm_temperature: float = Field(
        default=0.0, ge=0.0, le=2.0, description="LLM temperature"
    )
    top_k_retrieval: int = Field(
        default=5, ge=1, le=20, description="Number of chunks to retrieve"
    )
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Max tokens for LLM response")
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within valid range."""
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class VectorStoreConfig(BaseModel):
    """Configuration for vector store."""

    persist_directory: str = Field(
        default="./data/chroma", description="Directory for vector store persistence"
    )
    collection_name: str = Field(
        default="property_documents", description="Collection name"
    )
    distance_metric: str = Field(default="cosine", description="Distance metric for similarity")

    @field_validator("distance_metric")
    @classmethod
    def validate_distance_metric(cls, v: str) -> str:
        """Validate distance metric is supported."""
        valid_metrics = ["cosine", "euclidean", "dot"]
        if v not in valid_metrics:
            raise ValueError(f"Distance metric must be one of {valid_metrics}")
        return v


class PipelineConfig(BaseModel):
    """Configuration for pipeline orchestration."""

    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(
        default=1.0, ge=0.1, le=60.0, description="Initial retry delay in seconds"
    )
    exponential_backoff: bool = Field(
        default=True, description="Use exponential backoff for retries"
    )
    batch_concurrency: int = Field(
        default=5, ge=1, le=50, description="Maximum concurrent batch processing"
    )
    rate_limit_per_minute: int = Field(
        default=60, ge=1, le=1000, description="API rate limit per minute"
    )
    timeout: float = Field(
        default=300.0, ge=10.0, le=3600.0, description="Pipeline timeout in seconds"
    )

    @field_validator("max_retries")
    @classmethod
    def validate_retries(cls, v: int) -> int:
        """Validate retry count is reasonable."""
        if v < 0 or v > 10:
            raise ValueError("Max retries must be between 0 and 10")
        return v


class APIConfig(BaseModel):
    """Configuration for external API credentials."""

    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")

    @model_validator(mode="after")
    def validate_at_least_one_key(self) -> "APIConfig":
        """Validate at least one API key is provided."""
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError("At least one API key (OpenAI or Anthropic) must be provided")
        return self


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_file: str = Field(default="./logs/extraction.log", description="Log file path")
    log_to_console: bool = Field(default=True, description="Enable console logging")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )


class Settings(BaseSettings):
    """Application settings loaded from environment variables or config files."""

    ocr: OCRConfig = Field(default_factory=OCRConfig)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"


class ConfigurationManager:
    """Manages configuration loading, validation, and runtime overrides."""

    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to JSON configuration file
            env_file: Path to .env file
        """
        self._config_path = config_path
        self._env_file = env_file or ".env"
        self._settings: Optional[Settings] = None
        self._runtime_overrides: Dict[str, Any] = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from files and environment variables."""
        try:
            # Start with defaults
            config_dict: Dict[str, Any] = {}

            # Load from JSON file if provided
            if self._config_path and os.path.exists(self._config_path):
                with open(self._config_path, "r") as f:
                    config_dict = json.load(f)

            # Load from environment variables (overrides file config)
            if os.path.exists(self._env_file):
                from dotenv import load_dotenv
                load_dotenv(self._env_file)

            # Create settings with merged configuration
            self._settings = Settings(**config_dict)

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e

    def get_settings(self) -> Settings:
        """
        Get current settings.

        Returns:
            Settings object with current configuration

        Raises:
            ConfigurationError: If configuration is not loaded
        """
        if self._settings is None:
            raise ConfigurationError("Configuration not loaded")
        return self._settings

    def reload_configuration(self) -> None:
        """
        Reload configuration from files without restarting.

        This enables hot configuration reload as per requirement 7.5.

        Raises:
            ConfigurationError: If reload fails
        """
        try:
            old_settings = self._settings
            self._load_configuration()
            # Apply any runtime overrides
            if self._runtime_overrides:
                self._apply_overrides(self._runtime_overrides)
        except Exception as e:
            # Restore old settings on failure
            self._settings = old_settings
            raise ConfigurationError(f"Failed to reload configuration: {str(e)}") from e

    def override_settings(self, overrides: Dict[str, Any]) -> Settings:
        """
        Apply runtime configuration overrides.

        This creates a new Settings instance with overrides applied,
        without modifying the base configuration.

        Args:
            overrides: Dictionary of configuration overrides

        Returns:
            New Settings object with overrides applied

        Raises:
            ConfigurationError: If overrides are invalid
        """
        try:
            if self._settings is None:
                raise ConfigurationError("Configuration not loaded")

            # Create a copy of current settings as dict
            current_dict = self._settings.model_dump()

            # Apply overrides
            self._deep_update(current_dict, overrides)

            # Create new settings with overrides
            return Settings(**current_dict)

        except Exception as e:
            raise ConfigurationError(f"Failed to apply overrides: {str(e)}") from e

    def _apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply overrides to current settings."""
        if self._settings is None:
            return

        current_dict = self._settings.model_dump()
        self._deep_update(current_dict, overrides)
        self._settings = Settings(**current_dict)

    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """
        Recursively update nested dictionary.

        Args:
            base: Base dictionary to update
            updates: Updates to apply
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[str] = []

        try:
            if self._settings is None:
                errors.append("Configuration not loaded")
                return errors

            # Pydantic validation happens automatically during model creation
            # Additional custom validations can be added here

            # Validate file paths exist
            if not os.path.exists(os.path.dirname(self._settings.logging.log_file)):
                errors.append(
                    f"Log directory does not exist: {os.path.dirname(self._settings.logging.log_file)}"
                )

            # Validate vector store directory
            persist_dir = self._settings.vector_store.persist_directory
            if not os.path.exists(persist_dir):
                try:
                    os.makedirs(persist_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create vector store directory: {str(e)}")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return errors

    def save_configuration(self, output_path: str) -> None:
        """
        Save current configuration to JSON file.

        Args:
            output_path: Path to save configuration

        Raises:
            ConfigurationError: If save fails
        """
        try:
            if self._settings is None:
                raise ConfigurationError("Configuration not loaded")

            config_dict = self._settings.model_dump()

            # Remove sensitive data
            if "api" in config_dict:
                if config_dict["api"].get("openai_api_key"):
                    config_dict["api"]["openai_api_key"] = "***REDACTED***"
                if config_dict["api"].get("anthropic_api_key"):
                    config_dict["api"]["anthropic_api_key"] = "***REDACTED***"

            with open(output_path, "w") as f:
                json.dump(config_dict, f, indent=2)

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}") from e


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager(
    config_path: Optional[str] = None, env_file: Optional[str] = None
) -> ConfigurationManager:
    """
    Get or create the global configuration manager instance.

    Args:
        config_path: Path to JSON configuration file
        env_file: Path to .env file

    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager(config_path=config_path, env_file=env_file)
    return _config_manager


def get_settings() -> Settings:
    """
    Get current settings from global configuration manager.

    Returns:
        Settings object with current configuration
    """
    return get_config_manager().get_settings()
