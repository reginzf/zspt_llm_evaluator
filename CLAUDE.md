# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-KEN (AI Knowledge Evaluation) is a platform for evaluating LLM models against QA datasets. It provides tools for managing knowledge bases, QA data groups, running evaluations, and viewing reports.

**Architecture**: Python Flask backend + Vue 3 TypeScript frontend with PostgreSQL database.

## Development Commands

### Backend (Flask)

```bash
# Start the Flask server
python app.py
python app.py --host 0.0.0.0 --port 5001 --debug

# Or use the startup script
python scripts/start_backend.py

# Run tests
pytest tests/
pytest tests/test_environment_management.py -v
```

### Frontend (Vue 3)

```bash
cd frontend

# Install dependencies
npm install

# Development server (hot-reload)
npm run dev

# Build for production
npm run build

# Type check only
npm run type-check
```

### Full Stack Development

```bash
# Terminal 1: Start backend
python scripts/start_backend.py --debug

# Terminal 2: Start frontend dev server
cd frontend && npm run dev

# Access the application at http://localhost:5173
# API available at http://localhost:5001
```

## Project Structure

### Backend (`/` and `src/`)

- **`app.py`** - Flask application entry point, CORS config, Vue SPA routing
- **`src/flask_funcs/`** - API route blueprints
  - `qa_data.py` / `qa_data_group.py` - QA data management
  - `llm_model_routes.py` - LLM evaluation APIs
  - `local_knowledge*.py` - Knowledge base routes
  - `environment.py` - Environment/test configuration routes
  - `annotation_tasks.py` - Annotation task management
- **`src/sql_funs/`** - Database CRUD operations
  - `sql_base.py` - PostgreSQL connection pool and base operations
  - `*_crud.py` - Entity-specific database operations
- **`src/llm/`** - LLM evaluation logic
  - `api_agent_evaluator.py` - Main evaluation engine
  - `llm_agent_basic.py` - LLM interface wrappers
- **`src/label_studio_api/`** - Label Studio integration

### Frontend (`frontend/src/`)

- **`views/`** - Page components organized by feature
  - `qa/` - QA data group management
  - `llm/` - Model evaluation and reports
  - `knowledge/` - Knowledge base management
  - `environment/` - Test environment configuration
  - `annotation/` - Label Studio annotation tasks
- **`api/`** - Axios API client and endpoint definitions
- **`router/`** - Vue Router configuration
- **`types/`** - TypeScript type definitions

## Configuration

### Backend Configuration (`configs/settings.toml`)

Copy `configs/settings_example.toml` to `configs/settings.toml` and configure:

```toml
[default]
PROJECT_ROOT = '/path/to/project'

# PostgreSQL Database
SQL_HOST = 'localhost'
SQL_PORT = 5432
SQL_DB = 'label_studio'
SQL_USER = 'user'
SQL_PASSWORD = 'password'

# MinIO File Storage
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'admin123'
MINIO_BUCKET_NAME = 'knowledge-files'

# LLM API (DeepSeek)
DEEPSEEK_API_KEY = "sk-..."
DEEPSEEK_API_BASE = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

# Vector Model Path (for similarity calculations)
MODEL_PATH = '/path/to/bge-base-zh-v1.5'
```

### Frontend Environment

- `.env.development` - Development API endpoints
- `.env.production` - Production build settings

### CORS Configuration

Backend CORS origins are configured in `app.py`. For development with custom IPs:

```bash
# Allow all origins (development only!)
export CORS_ALLOW_ALL=true

# Or add specific origins
export CORS_ORIGINS="http://192.168.1.100:5173,http://10.0.0.5:5173"
```

## Database

The application uses PostgreSQL with SQLAlchemy/ psycopg2:

- **Connection Pool**: Initialized at startup via `PostgreSQLManager.initialize_pool()`
- **Main Schema**: `label_studio` database with tables for:
  - QA data groups and individual QA pairs
  - LLM models and evaluation reports
  - Knowledge bases and document chunks
  - Environments (test configurations)
  - Annotation tasks and Label Studio projects

### Key Database Operations

```python
from src.sql_funs.sql_base import PostgreSQLManager

# The manager uses singleton pattern per host
# Connection pool is shared across instances
PostgreSQLManager.initialize_pool(minconn=10, maxconn=50)
```

## Important Implementation Details

### Frontend Serving Mode

The backend can serve the Vue frontend in multiple modes controlled by `VUE_FRONTEND_MODE`:

- `auto` (default) - Detects if `frontend/dist/index.html` exists, serves it if found
- `force` - Always serve Vue frontend (error if not built)
- `disable` - Use legacy Flask templates (not recommended)

**For production deployment**: Build frontend first (`npm run build` in `frontend/`), then start backend.

### Request/Response Logging

All API requests are logged to `logs/request.log` with timing information. Error details go to `logs/error.log`.

### Label Studio Integration

The platform integrates with Label Studio for annotation workflows:
- Syncs projects and tasks between systems
- Supports importing annotated data back as QA pairs
- Configurable via environment settings

### LLM Evaluation Flow

1. QA data group selected + environment configuration
2. LLM model APIs called with prompts
3. Responses compared against ground truth using:
   - Exact match
   - Semantic similarity (BGE embeddings)
   - LLM-as-judge evaluation
4. Metrics calculated (accuracy, recall, F1 at various k values)
5. Reports stored and visualized in frontend

## Code Style

- **Backend**: PEP 8, use type hints where practical
- **Frontend**: Vue 3 Composition API with `<script setup>` syntax, TypeScript strict mode
