# Verification Scripts

This directory contains manual verification scripts for testing individual modules of the RAG system. These scripts are intended for development and debugging purposes.

## Available Scripts

- **verify_ocr.py** - Verifies OCR module functionality with sample PDF processing
- **verify_chunking.py** - Tests document chunking with various text inputs
- **verify_config.py** - Validates configuration management system
- **verify_output_formatter.py** - Tests output formatting and validation
- **verify_rag_engine.py** - Verifies RAG extraction engine (requires API keys)
- **verify_ragas_evaluator.py** - Tests RAGAS evaluation metrics (requires API keys)
- **verify_vector_store.py** - Validates vector store operations

## Running Verification Scripts

All scripts should be run from the repository root to ensure correct module imports:

```bash
# From repository root
python scripts/verify/verify_config.py
python scripts/verify/verify_ocr.py
python scripts/verify/verify_chunking.py
```

Some scripts require environment variables (API keys) to be set. See `.env.example` for required variables.

## Notes

- Scripts import from `src.*` packages, so they must be run from the repository root
- Sample data files are located in `data/samples/`
- These are development tools, not production test suites
