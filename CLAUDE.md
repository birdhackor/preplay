# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Prerender service** - a self-hosted alternative to prerender.io built with FastAPI + Playwright (Firefox). The service renders JavaScript-heavy web pages into static HTML for search engine crawlers and AI bots, improving SEO and AEO.

**Key Features:**
- Server-side rendering using Playwright with Firefox browser
- JWT-based authentication to prevent unauthorized access
- Simple in-memory caching with TTL (time-based expiration)
- Designed for Kubernetes deployment

The project uses Python 3.13.9+ and leverages modern Python packaging with `uv`.

## Development Commands

### Package Management
- Install dependencies: `uv sync`
- Add new dependency: `uv add <package-name>`
- Add dev dependency: `uv add --dev <package-name>`

### Code Quality
- Run linter/formatter: `uv run ruff check .`
- Auto-fix issues: `uv run ruff check --fix .`
- Format code: `uv run ruff format .`

### Playwright Setup
- Install Playwright: `uv add playwright`
- Install Firefox browser: `uv run playwright install firefox`

### Running the Application
- Development server: `uv run fastapi dev entry.py`
- Production server: `uv run gunicorn entry:app -c gunicorn.conf.py -k worker.ConfigurableUvicornWorker`

## Architecture

### Application Entry Points
- **entry.py**: Main entry point that imports the FastAPI app from the `main` package
- **worker.py**: Custom Gunicorn worker configuration extending UvicornWorker
- **gunicorn.conf.py**: Gunicorn configuration with custom signal handling

### Core Application Structure (`main/`)
- **main.py**: FastAPI application instance with ORJSONResponse as default response class
- **config.py**: Pydantic-based settings management with JWT keys configuration. Settings are cached using `lru_cache`
- **logging.py**: Custom logging setup using Loguru that propagates to Gunicorn/Uvicorn/Celery loggers based on runtime environment
- **render.py**: Playwright-based rendering service (to be implemented)
- **cache.py**: Time-based cache decorator for rendered HTML (to be implemented)
- **auth.py**: JWT authentication middleware (to be implemented)

### Key Technical Details
- Uses custom `ConfigurableUvicornWorker` that reads `SCRIPT_NAME` or `ROOT_PATH` environment variables for reverse proxy support
- Enables proxy headers and forwarded IPs handling
- Logging is integrated with Loguru but propagates to appropriate framework loggers (Gunicorn, Uvicorn, or Celery) depending on execution context
- Settings expect `jwt_keys` as a dict mapping from string to bytes

### API Endpoints (Planned)

- `GET /render?url=<target_url>` - Main rendering endpoint (requires JWT auth)
- `GET /health` - Kubernetes liveness probe
- `GET /readiness` - Kubernetes readiness probe

### Environment Variables

- `JWT_KEYS` - JSON object mapping key IDs to secret keys (string to bytes dict)
- `SCRIPT_NAME` / `ROOT_PATH` - Reverse proxy path prefix (optional)
- `CACHE_TTL` - Cache time-to-live in seconds (default: 86400 = 24 hours)
- `RENDER_TIMEOUT` - Page render timeout in seconds (default: 30)

### Linting Configuration

- Target Python version: 3.13
- Excludes `migrations` directory
- Extends Ruff with import sorting ("I" rules)

## Kubernetes Deployment (Planned)

### Build Docker Image

```bash
docker build -t preplay:latest .
```

### Deploy to Kubernetes

```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Required Kubernetes Resources

- **Secret**: JWT keys configuration
- **Deployment**: Application pods with resource limits
- **Service**: ClusterIP service for internal routing
- **Ingress** (optional): External access configuration
