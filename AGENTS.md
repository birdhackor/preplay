# AGENTS.md (CLAUDE.md)

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
- Run command: `uv run <cmd>`

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

- **main.py**: FastAPI application instance with ORJSONResponse, lifespan management, and API endpoints
- **config.py**: Pydantic-based settings management with JWT keys, render_timeout, cache_ttl, cache_max_entries. Settings are cached using `lru_cache`
- **logging.py**: Custom logging setup using Loguru that propagates to Gunicorn/Uvicorn/Celery loggers based on runtime environment
- **render.py**: Playwright-based rendering service with singleton Firefox browser instance
- **cache.py**: In-memory TTL cache with LRU eviction strategy (max 50 entries by default)
- **auth.py**: JWT authentication middleware using FastAPI HTTPBearer
- **helpers.py**: Utility functions including URL normalization (removes fragment, sorts query params)
- **dependencies.py**: FastAPI dependency injection providers for cache and render service

### Key Technical Details

- Uses custom `ConfigurableUvicornWorker` that reads `SCRIPT_NAME` or `ROOT_PATH` environment variables for reverse proxy support
- Enables proxy headers and forwarded IPs handling
- Logging is integrated with Loguru but propagates to appropriate framework loggers (Gunicorn, Uvicorn, or Celery) depending on execution context
- Settings expect `jwt_keys` as a dict mapping from string to bytes (Pydantic automatically converts JSON string values to bytes)
- **JWT Authentication**: Integrated at route level using `dependencies=[Depends(verify_jwt_token)]` parameter
- **Browser Lifecycle**: Managed via FastAPI lifespan context manager, ensuring graceful startup/shutdown
- **URL Normalization**: Leverages Pydantic `HttpUrl` properties (scheme, host, port, path, query) for efficient cache key generation
- **Cache Strategy**: Uses `time.monotonic()` for TTL, implements LRU eviction when max_entries is reached
- **Rendering Strategy**: Waits for `networkidle` state to ensure JavaScript execution completes (suitable for SPA applications)

### API Endpoints

- `GET /render?url=<target_url>` - Main rendering endpoint (requires JWT auth)
  - Returns: HTML content with `X-Cache` and `X-Rendered-By` headers
  - Validates URL using Pydantic `HttpUrl` (only http/https schemes allowed)
  - Normalizes URLs to improve cache hit rate (removes fragments, sorts query parameters)
  - Error responses: 403 (auth failure), 422 (invalid URL), 500 (render error), 504 (timeout)
- `GET /health` - Kubernetes liveness probe (always returns 200 OK)
- `GET /readiness` - Kubernetes readiness probe (503 if browser not initialized)

### Environment Variables

- `JWT_KEYS` - JSON object mapping key IDs to secret keys, e.g., `{"default": "testsecret"}` (Pydantic converts to dict[str, bytes])
- `SCRIPT_NAME` / `ROOT_PATH` - Reverse proxy path prefix (optional)
- `CACHE_TTL` - Cache time-to-live in seconds (default: 86400 = 24 hours)
- `CACHE_MAX_ENTRIES` - Maximum number of cache entries (default: 50, LRU eviction when exceeded)
- `RENDER_TIMEOUT` - Page render timeout in seconds (default: 30)

### Linting Configuration

- Target Python version: 3.13
- Excludes `migrations` directory
- Extends Ruff with import sorting ("I" rules)

## Usage Examples

### Local Development

1. **Install dependencies and Firefox browser:**

   ```bash
   uv sync
   uv run playwright install firefox
   ```

2. **Set environment variables:**

   ```bash
   export JWT_KEYS='{"default": "testsecret"}'
   export RENDER_TIMEOUT=30
   export CACHE_TTL=3600
   export CACHE_MAX_ENTRIES=50
   ```

3. **Start development server:**

   ```bash
   uv run fastapi dev entry.py
   ```

4. **Generate JWT token for testing:**

   ```bash
   uv run python -c "
   import jwt
   token = jwt.encode({'sub': 'test'}, b'testsecret', algorithm='HS256')
   print(token)
   "
   ```

5. **Test the endpoints:**

   ```bash
   # Health check
   curl http://localhost:8000/health

   # Readiness check
   curl http://localhost:8000/readiness

   # Render a page (replace TOKEN with generated token)
   curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/render?url=https://example.com"

   # Check cache header
   curl -i -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/render?url=https://example.com" \
     | grep X-Cache
   ```

### Production Deployment

```bash
# Start with Gunicorn
export JWT_KEYS='{"prod": "your-secret-key-here"}'
uv run gunicorn entry:app \
  -c gunicorn.conf.py \
  -k worker.ConfigurableUvicornWorker \
  --workers 4
```

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

## Others

Always check newest docs with context7.
