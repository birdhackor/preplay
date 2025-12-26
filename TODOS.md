# Prerender Service Implementation TODOs

## ✅ Phase 1: Documentation Preparation

- [x] Update CLAUDE.md with project goals and architecture
- [x] Create TODOS.md with all implementation tasks

## ✅ Phase 2: Infrastructure Setup

### Task 3: Add Dependencies

- [x] Install Playwright: `uv add playwright`
- [x] Install Firefox browser: `uv run playwright install firefox`
- [x] Verify Playwright installation works

### Task 4: JWT Authentication Middleware

- [x] Create `main/auth.py` module
- [x] Implement FastAPI dependency for JWT token verification using HTTPBearer
- [x] Use existing `jwt_keys` from config.py for validation
- [x] Return 403 for unauthorized requests
- [x] HTTPBearer handles missing/invalid Authorization header automatically
- [ ] Add unit tests for authentication

## ✅ Phase 3: Core Rendering Functionality

### Task 5: Playwright Rendering Service

- [x] Create `main/render.py` module
- [x] Implement `RenderService` class to manage Playwright browser instance
- [x] Create browser context and page management
- [x] Implement page loading with configurable timeout (default: 30s)
- [x] Wait for network idle state
- [x] Extract and return complete rendered HTML
- [x] Handle graceful browser shutdown
- [x] Add error handling for browser failures
- [x] Integrate with FastAPI lifespan for proper startup/shutdown

### Task 6: Simple Cache Layer

- [x] Create `main/cache.py` module
- [x] Implement time-based cache using Python dict + timestamp (using `time.monotonic()`)
- [x] Implement LRU eviction strategy with max_entries limit
- [x] URL as key, HTML + timestamp as value
- [x] Implement cache expiration check (lazy cleanup)
- [x] Make TTL configurable via environment variable

## ✅ Phase 4: API Endpoints

### Task 7: Create Rendering API Endpoints

- [x] Add `/render` endpoint in main.py
- [x] Accept `url` query parameter (using Pydantic HttpUrl)
- [x] Integrate JWT authentication dependency (via dependencies parameter)
- [x] Integrate rendering service (via dependency injection)
- [x] Integrate caching layer (via dependency injection)
- [x] Return rendered HTML with appropriate headers (X-Cache, X-Rendered-By)
- [x] Add `/health` endpoint for Kubernetes liveness probe
- [x] Add `/readiness` endpoint for Kubernetes readiness probe

### Task 8: Error Handling & Validation

- [x] Use Pydantic HttpUrl for URL validation (built-in validation)
- [x] URL normalization helper (remove fragment, sort query params)
- [x] Handle render timeout errors gracefully
- [x] Handle Playwright failures with proper error messages
- [x] Return appropriate HTTP status codes (403, 422, 500, 503, 504)
- [x] Add comprehensive error logging

## ✅ Phase 5: Testing and Quality

### Task 9: Testing Strategy and Coverage

- [x] Define testing strategy: stub RenderService for most API tests; keep small real Playwright suite for sanity
  - task-note: Use FastAPI dependency_overrides to inject a stub render service and small TTL cache; exercise 200/403 and X-Cache HIT/MISS without launching browser
- [x] Add unit tests for authentication (9 tests in test_auth.py)
- [x] Add unit tests for cache layer (10 tests in test_cache.py)
- [x] Add unit tests for helpers (9 tests in test_helpers.py)
- [x] Add integration tests for rendering service (7 tests in test_render_service.py, marked as slow)
- [x] Add end-to-end API tests (3 tests in test_full_render_flow.py, marked as e2e and slow)
- [x] Implement API tests with stubbed render service (12 tests in test_api.py)
  - task-note: Used TestClient with custom FastAPI app and stub lifespan; tested auth, cache behavior, normalized URL flow
- [x] Add slow smoke tests using real Playwright
  - task-note: Real Playwright tests run against data: URLs and example.com; marked with @pytest.mark.slow
- [x] Test with sample JavaScript-heavy websites (test_render_javascript_page validates JS execution)

**Test Results**:

- Total: 55 tests (all passing)
- Unit tests: 28 tests (fast, < 3 seconds)
- Integration tests (stubbed): 12 tests (fast)
- Integration tests (real Playwright): 7 tests (slow, ~15 seconds)
- E2E tests: 3 tests (slow, uses real Playwright)
- **Code coverage: 88%** (exceeds 85% target)
  - main/auth.py: 100%
  - main/cache.py: 98%
  - main/config.py: 100%
  - main/dependencies.py: 100%
  - main/helpers.py: 100%
  - main/main.py: 78%
  - main/render.py: 82%

**Test Commands**:

```bash
# Fast tests only (unit + stubbed integration)
uv run pytest tests -m "not slow and not e2e" -v

# Full test suite with coverage
uv run pytest tests --cov=main --cov-report=html -v

# Only slow tests
uv run pytest tests -m "slow or e2e" -v
```

## Phase 6: Kubernetes Deployment Preparation

### Task 10: Create Dockerfile

- [ ] Create Dockerfile with Python 3.13 base image
- [ ] Install uv package manager
- [ ] Copy and install project dependencies
- [ ] Install Playwright and Firefox browser
- [ ] Configure non-root user for security
- [ ] Optimize image size (multi-stage build if needed)
- [ ] Test Docker build locally

### Task 11: Kubernetes Configuration Files

- [ ] Create `k8s/` directory
- [ ] Create `k8s/secret.yaml` for JWT keys
- [ ] Create `k8s/deployment.yaml` with:
  - Resource limits (CPU/memory)
  - Environment variables
  - Liveness probe configuration
  - Readiness probe configuration
- [ ] Create `k8s/service.yaml` (ClusterIP)
- [ ] (Optional) Create `k8s/ingress.yaml` for external access
- [ ] Add documentation for deployment process

### Task 12: Lifecycle Management

- [ ] Implement graceful shutdown in application
- [ ] Close browser instances on shutdown
- [ ] Configure liveness probe path and settings
- [ ] Configure readiness probe path and settings
- [ ] Test probes locally
- [ ] Add pre-stop hook if needed

## Additional Tasks

### Documentation

- [ ] Add API usage examples to README
- [ ] Document JWT token generation process
- [ ] Add troubleshooting guide
- [ ] Document environment variable configuration

### Performance & Monitoring

- [ ] Add Prometheus metrics endpoint (optional)
- [ ] Monitor browser memory usage
- [ ] Implement browser instance pooling if needed
- [ ] Add request rate limiting (optional)
- [ ] Monitor cache hit/miss rates

---

## ✅ Phase 3 & 4 Implementation Summary

### New Files Created

1. **`main/render.py`** - Playwright rendering service with singleton browser instance
2. **`main/cache.py`** - In-memory TTL cache with LRU eviction (max 50 entries)
3. **`main/helpers.py`** - URL normalization utility (removes fragments, sorts query params)
4. **`main/dependencies.py`** - FastAPI dependency injection providers

### Modified Files

1. **`main/config.py`** - Added `render_timeout`, `cache_ttl`, `cache_max_entries`
2. **`main/main.py`** - Integrated lifespan, added 3 API endpoints with proper error handling

### Key Features Implemented

- ✅ **JWT Authentication**: Multi-key support, integrated at route level via `dependencies` parameter
- ✅ **URL Normalization**: Leverages Pydantic `HttpUrl` properties for efficient caching
- ✅ **LRU Cache**: Prevents memory overflow with configurable max entries
- ✅ **Error Handling**: Comprehensive HTTP status codes (403, 422, 500, 503, 504)
- ✅ **Kubernetes Ready**: `/health` and `/readiness` probes implemented
- ✅ **FastAPI Lifespan**: Graceful browser startup/shutdown management

### Tested Scenarios

- ✅ Missing JWT token → 403 Forbidden
- ✅ Invalid JWT token → 403 Forbidden
- ✅ Invalid URL format → 422 Unprocessable Content
- ✅ Successful rendering → 200 OK with HTML content
- ✅ Cache hit/miss → X-Cache header correctly set

---

## Implementation Notes

- **Cache Strategy**: Using Python dict + `time.monotonic()`, LRU eviction, no external dependencies
- **Browser**: Firefox via Playwright (singleton instance, networkidle wait strategy)
- **Authentication**: JWT with multi-key support from config.py
- **Deployment Target**: Kubernetes
- **Language**: Python 3.13+
- **Framework**: FastAPI with async/await
