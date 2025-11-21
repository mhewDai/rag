# Configuration Management System

The Property Data Extraction System uses a comprehensive configuration management system that supports multiple configuration sources, validation, and runtime overrides.

## Features

- **Structured Configuration**: Organized into logical sections (OCR, Chunking, RAG, Pipeline, etc.)
- **Multiple Sources**: Load from environment variables, JSON files, or Python dictionaries
- **Validation**: Automatic validation with clear error messages
- **Runtime Overrides**: Override configuration for specific requests without modifying base config
- **Hot Reload**: Reload configuration without restarting the system
- **Type Safety**: Full type hints and Pydantic validation

## Configuration Sections

### OCR Configuration

Controls optical character recognition settings:

```python
ocr:
  tesseract_cmd: "/usr/local/bin/tesseract"  # Path to Tesseract
  language: "eng"                             # OCR language code
  dpi: 300                                    # DPI for image processing (72-600)
  preprocess: true                            # Enable preprocessing
  denoise: true                               # Enable denoising
  deskew: true                                # Enable deskewing
  contrast_enhancement: true                  # Enable contrast enhancement
```

### Chunking Configuration

Controls document chunking behavior:

```python
chunk:
  chunk_size: 800                # Maximum chunk size in tokens (100-2000)
  chunk_overlap: 100             # Overlap between chunks (0-500)
  strategy: "sentence-aware"     # Chunking strategy
  min_chunk_size: 50             # Minimum chunk size (10+)
```

### RAG Configuration

Controls retrieval-augmented generation:

```python
rag:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  llm_model: "gpt-4"
  llm_temperature: 0.0           # Temperature (0.0-2.0)
  top_k_retrieval: 5             # Number of chunks to retrieve (1-20)
  max_tokens: 1000               # Max tokens for LLM response (100-4000)
  confidence_threshold: 0.5      # Minimum confidence (0.0-1.0)
```

### Vector Store Configuration

Controls vector database settings:

```python
vector_store:
  persist_directory: "./data/chroma"
  collection_name: "property_documents"
  distance_metric: "cosine"      # cosine, euclidean, or dot
```

### Pipeline Configuration

Controls pipeline orchestration:

```python
pipeline:
  max_retries: 3                 # Maximum retry attempts (0-10)
  retry_delay: 1.0               # Initial retry delay in seconds
  exponential_backoff: true      # Use exponential backoff
  batch_concurrency: 5           # Max concurrent batch processing (1-50)
  rate_limit_per_minute: 60      # API rate limit (1-1000)
  timeout: 300.0                 # Pipeline timeout in seconds
```

### API Configuration

API credentials (never commit these!):

```python
api:
  openai_api_key: "your-key-here"
  anthropic_api_key: "your-key-here"
```

### Logging Configuration

Controls logging behavior:

```python
logging:
  log_level: "INFO"              # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: "./logs/extraction.log"
  log_to_console: true
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Usage Examples

### Basic Usage

```python
from src.config import get_settings

# Get current settings
settings = get_settings()

# Access configuration values
print(f"OCR DPI: {settings.ocr.dpi}")
print(f"Chunk Size: {settings.chunk.chunk_size}")
print(f"LLM Model: {settings.rag.llm_model}")
```

### Load from Environment Variables

Create a `.env` file (use nested delimiter `__`):

```bash
# .env
API__OPENAI_API_KEY=your_key_here
OCR__DPI=350
CHUNK__CHUNK_SIZE=1000
RAG__LLM_TEMPERATURE=0.5
```

Then load:

```python
from src.config import get_config_manager

manager = get_config_manager(env_file=".env")
settings = manager.get_settings()
```

### Load from JSON File

Create a `config.json` file:

```json
{
  "ocr": {
    "dpi": 350,
    "language": "eng"
  },
  "chunk": {
    "chunk_size": 1000,
    "chunk_overlap": 150
  },
  "rag": {
    "llm_temperature": 0.5
  }
}
```

Then load:

```python
from src.config import load_from_file

settings = load_from_file("config.json")
```

### Runtime Configuration Override

Override configuration for a specific request:

```python
from src.config import get_config_manager

manager = get_config_manager()

# Apply overrides for this request only
overrides = {
    "chunk": {"chunk_size": 1200},
    "rag": {"llm_temperature": 0.7, "top_k_retrieval": 10}
}

custom_settings = manager.override_settings(overrides)

# Use custom_settings for this request
# Base settings remain unchanged
```

### Hot Configuration Reload

Reload configuration without restarting:

```python
from src.config import get_config_manager

manager = get_config_manager()

# ... system is running ...

# Configuration file was modified externally
manager.reload_configuration()

# New settings are now active
settings = manager.get_settings()
```

### Configuration Validation

Validate configuration before use:

```python
from src.config import get_config_manager

manager = get_config_manager()
errors = manager.validate_configuration()

if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

### Create Default Configuration

Generate a default configuration file:

```python
from src.config import create_default_config_file

create_default_config_file("my_config.json")
# Edit my_config.json and load it
```

## Configuration Priority

When multiple configuration sources are present, they are merged in this order (later overrides earlier):

1. Default values (defined in code)
2. JSON configuration file
3. Environment variables
4. Runtime overrides

## Validation Rules

The configuration system enforces these validation rules:

### OCR
- DPI must be between 72 and 600
- Language code cannot be empty

### Chunking
- Chunk overlap must be less than chunk size
- Minimum chunk size must be less than or equal to chunk size
- Chunk size must be between 100 and 2000 tokens

### RAG
- Temperature must be between 0.0 and 2.0
- Top-K retrieval must be between 1 and 20
- Confidence threshold must be between 0.0 and 1.0

### Pipeline
- Max retries must be between 0 and 10
- Batch concurrency must be between 1 and 50
- Rate limit must be between 1 and 1000

### API
- At least one API key (OpenAI or Anthropic) must be provided

## Error Handling

The configuration system raises `ConfigurationError` for:

- Invalid configuration values
- Missing required fields
- File not found
- Invalid JSON syntax
- Validation failures

Example:

```python
from src.config import ConfigurationError, load_from_file

try:
    settings = load_from_file("config.json")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Best Practices

1. **Never commit API keys**: Use environment variables or `.env` files (add to `.gitignore`)
2. **Use JSON for complex configs**: Easier to manage than many environment variables
3. **Validate early**: Call `validate_configuration()` at startup
4. **Use runtime overrides**: For request-specific settings without modifying base config
5. **Document custom values**: Add comments explaining non-default settings
6. **Test configuration changes**: Use `validate_config_file()` before deploying

## Environment Variable Naming

For nested configuration, use double underscore (`__`) as delimiter:

```bash
# Top level
API__OPENAI_API_KEY=key

# Nested: ocr.dpi
OCR__DPI=350

# Nested: chunk.chunk_size
CHUNK__CHUNK_SIZE=1000

# Nested: rag.llm_temperature
RAG__LLM_TEMPERATURE=0.5
```

## Complete Example

```python
from src.config import (
    ConfigurationManager,
    ConfigurationError,
    load_from_file,
)

# Initialize with JSON config
try:
    manager = ConfigurationManager(config_path="config.json")
    
    # Validate configuration
    errors = manager.validate_configuration()
    if errors:
        raise ConfigurationError(f"Invalid config: {errors}")
    
    # Get base settings
    settings = manager.get_settings()
    
    # Process a document with custom settings
    overrides = {"rag": {"llm_temperature": 0.7}}
    custom_settings = manager.override_settings(overrides)
    
    # Use custom_settings for this specific extraction
    # ...
    
    # Reload if config file changes
    manager.reload_configuration()
    
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    exit(1)
```

## See Also

- `examples/config_usage.py` - Complete usage examples
- `config.example.json` - Example JSON configuration
- `.env.example` - Example environment variables
