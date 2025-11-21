#!/usr/bin/env python3
"""Quick verification script for configuration management system."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    Settings,
    OCRConfig,
    ChunkConfig,
    RAGConfig,
    APIConfig,
    ConfigurationManager,
    ConfigurationError,
    load_from_dict,
)


def verify_basic_creation():
    """Verify basic settings creation."""
    print("✓ Testing basic settings creation...")
    settings = Settings(api=APIConfig(openai_api_key="test_key"))
    assert settings.ocr.dpi == 300
    assert settings.chunk.chunk_size == 800
    print("  ✓ Default values loaded correctly")


def verify_validation():
    """Verify validation works."""
    print("✓ Testing validation...")
    
    # Valid config
    config = OCRConfig(dpi=300)
    assert config.dpi == 300
    print("  ✓ Valid config accepted")
    
    # Invalid config
    try:
        OCRConfig(dpi=50)  # Too low
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  ✓ Invalid config rejected")


def verify_nested_config():
    """Verify nested configuration."""
    print("✓ Testing nested configuration...")
    
    config_dict = {
        "api": {"openai_api_key": "test"},
        "ocr": {"dpi": 350, "language": "eng"},
        "chunk": {"chunk_size": 1000, "chunk_overlap": 150},
        "rag": {"llm_temperature": 0.5, "top_k_retrieval": 10}
    }
    
    settings = load_from_dict(config_dict)
    assert settings.ocr.dpi == 350
    assert settings.chunk.chunk_size == 1000
    assert settings.rag.llm_temperature == 0.5
    print("  ✓ Nested configuration loaded correctly")


def verify_runtime_override():
    """Verify runtime overrides."""
    print("✓ Testing runtime overrides...")
    
    # Create a temporary config
    config_dict = {
        "api": {"openai_api_key": "test"},
        "chunk": {"chunk_size": 800}
    }
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_path = f.name
    
    try:
        manager = ConfigurationManager(config_path=temp_path)
        
        # Apply override
        overrides = {"chunk": {"chunk_size": 1200}}
        custom = manager.override_settings(overrides)
        
        assert custom.chunk.chunk_size == 1200
        assert manager.get_settings().chunk.chunk_size == 800  # Original unchanged
        print("  ✓ Runtime overrides work correctly")
    finally:
        import os
        os.unlink(temp_path)


def verify_all_config_sections():
    """Verify all configuration sections exist."""
    print("✓ Testing all configuration sections...")
    
    settings = Settings(api=APIConfig(openai_api_key="test"))
    
    # Check all sections exist
    assert hasattr(settings, 'ocr')
    assert hasattr(settings, 'chunk')
    assert hasattr(settings, 'rag')
    assert hasattr(settings, 'vector_store')
    assert hasattr(settings, 'pipeline')
    assert hasattr(settings, 'api')
    assert hasattr(settings, 'logging')
    
    print("  ✓ All configuration sections present")
    
    # Check key fields
    assert settings.ocr.tesseract_cmd is not None
    assert settings.chunk.chunk_size > 0
    assert settings.rag.llm_model is not None
    assert settings.pipeline.max_retries >= 0
    print("  ✓ All sections have required fields")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("Configuration Management System Verification")
    print("=" * 60 + "\n")
    
    try:
        verify_basic_creation()
        verify_validation()
        verify_nested_config()
        verify_runtime_override()
        verify_all_config_sections()
        
        print("\n" + "=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60 + "\n")
        
        print("Configuration system is working correctly.")
        print("\nKey features verified:")
        print("  • Configuration data models for OCR, chunking, RAG, and pipeline")
        print("  • Configuration loading from files and dictionaries")
        print("  • Configuration validation with clear error messages")
        print("  • Runtime configuration override mechanism")
        print("\nSee docs/CONFIGURATION.md for complete documentation.")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
