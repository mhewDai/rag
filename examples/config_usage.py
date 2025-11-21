"""Example usage of the configuration management system."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    ConfigurationManager,
    get_config_manager,
    get_settings,
    load_from_file,
    create_default_config_file,
)


def example_basic_usage():
    """Example: Basic configuration usage."""
    print("=== Basic Configuration Usage ===\n")
    
    # Get configuration manager (loads from .env by default)
    manager = get_config_manager()
    settings = manager.get_settings()
    
    print(f"OCR DPI: {settings.ocr.dpi}")
    print(f"Chunk Size: {settings.chunk.chunk_size}")
    print(f"LLM Model: {settings.rag.llm_model}")
    print(f"Max Retries: {settings.pipeline.max_retries}")
    print()


def example_runtime_override():
    """Example: Runtime configuration override."""
    print("=== Runtime Configuration Override ===\n")
    
    manager = get_config_manager()
    
    # Get base settings
    base_settings = manager.get_settings()
    print(f"Base chunk size: {base_settings.chunk.chunk_size}")
    
    # Apply runtime overrides for a specific request
    overrides = {
        "chunk": {"chunk_size": 1200, "chunk_overlap": 150},
        "rag": {"llm_temperature": 0.7, "top_k_retrieval": 10}
    }
    
    custom_settings = manager.override_settings(overrides)
    print(f"Overridden chunk size: {custom_settings.chunk.chunk_size}")
    print(f"Overridden temperature: {custom_settings.rag.llm_temperature}")
    print(f"Overridden top_k: {custom_settings.rag.top_k_retrieval}")
    
    # Base settings remain unchanged
    print(f"Base settings still: {base_settings.chunk.chunk_size}")
    print()


def example_hot_reload():
    """Example: Hot configuration reload."""
    print("=== Hot Configuration Reload ===\n")
    
    manager = get_config_manager()
    
    print("Initial settings loaded")
    settings = manager.get_settings()
    print(f"Current chunk size: {settings.chunk.chunk_size}")
    
    # Simulate configuration change (in real scenario, config file would be modified)
    print("\nReloading configuration...")
    manager.reload_configuration()
    
    settings = manager.get_settings()
    print(f"Reloaded chunk size: {settings.chunk.chunk_size}")
    print()


def example_validation():
    """Example: Configuration validation."""
    print("=== Configuration Validation ===\n")
    
    manager = get_config_manager()
    
    errors = manager.validate_configuration()
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    print()


def example_load_from_file():
    """Example: Load configuration from JSON file."""
    print("=== Load from JSON File ===\n")
    
    config_file = "config.example.json"
    
    if Path(config_file).exists():
        try:
            settings = load_from_file(config_file)
            print(f"Loaded from {config_file}")
            print(f"OCR Language: {settings.ocr.language}")
            print(f"Vector Store Directory: {settings.vector_store.persist_directory}")
            print(f"Batch Concurrency: {settings.pipeline.batch_concurrency}")
        except Exception as e:
            print(f"Error loading config: {e}")
    else:
        print(f"Config file {config_file} not found")
    print()


def example_create_default_config():
    """Example: Create default configuration file."""
    print("=== Create Default Configuration ===\n")
    
    output_file = "my_config.json"
    
    try:
        create_default_config_file(output_file)
        print(f"Created default configuration at {output_file}")
        print("You can now edit this file and load it with load_from_file()")
    except Exception as e:
        print(f"Error creating config: {e}")
    print()


def example_access_nested_config():
    """Example: Access nested configuration values."""
    print("=== Access Nested Configuration ===\n")
    
    settings = get_settings()
    
    # Access OCR settings
    print("OCR Configuration:")
    print(f"  Tesseract Command: {settings.ocr.tesseract_cmd}")
    print(f"  Language: {settings.ocr.language}")
    print(f"  DPI: {settings.ocr.dpi}")
    print(f"  Preprocessing: {settings.ocr.preprocess}")
    
    # Access RAG settings
    print("\nRAG Configuration:")
    print(f"  Embedding Model: {settings.rag.embedding_model}")
    print(f"  LLM Model: {settings.rag.llm_model}")
    print(f"  Temperature: {settings.rag.llm_temperature}")
    print(f"  Top-K Retrieval: {settings.rag.top_k_retrieval}")
    
    # Access Pipeline settings
    print("\nPipeline Configuration:")
    print(f"  Max Retries: {settings.pipeline.max_retries}")
    print(f"  Retry Delay: {settings.pipeline.retry_delay}s")
    print(f"  Exponential Backoff: {settings.pipeline.exponential_backoff}")
    print(f"  Batch Concurrency: {settings.pipeline.batch_concurrency}")
    print()


if __name__ == "__main__":
    print("Configuration Management System Examples\n")
    print("=" * 50)
    print()
    
    try:
        example_basic_usage()
        example_access_nested_config()
        example_runtime_override()
        example_validation()
        example_load_from_file()
        example_hot_reload()
        # example_create_default_config()  # Uncomment to create a config file
        
        print("=" * 50)
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
