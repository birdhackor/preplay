# Prerender Service Implementation TODOs

## ✅ Phase 1: Documentation Preparation

- [x] Update CLAUDE.md with project goals and architecture
- [x] Create TODOS.md with all implementation tasks

## ✅ Phase 2: Infrastructure Setup

### Task 3: Add Dependencies

- [x] Install Playwright: `uv add playwright`
- [x] Install Firefox browser: `uv run playwright install firefox`
- [ ] Verify Playwright installation works

### Task 4: JWT Authentication Middleware

- [x] Create `main/auth.py` module
- [x] Implement FastAPI dependency for JWT token verification using HTTPBearer
- [x] Use existing `jwt_keys` from config.py for validation
- [x] Return 403 for unauthorized requests
- [x] HTTPBearer handles missing/invalid Authorization header automatically
- [ ] Add unit tests for authentication

## Phase 3: Core Rendering Functionality (In Progress)

### Task 5: Playwright Rendering Service

- [ ] Create `main/render.py` module (drafted, needs review)
- [ ] Implement `RenderService` class to manage Playwright browser instance
- [ ] Create browser context and page management
- [ ] Implement page loading with configurable timeout (default: 30s)
- [ ] Wait for network idle state
- [ ] Extract and return complete rendered HTML
- [ ] Handle graceful browser shutdown
- [ ] Add error handling for browser failures
- [ ] Integrate with FastAPI lifespan for proper startup/shutdown

### Task 6: Simple Cache Layer

- [ ] Create `main/cache.py` module
- [ ] Implement time-based cache using Python dict + timestamp
- [ ] Create cache decorator with TTL support
- [ ] URL as key, HTML + timestamp as value
- [ ] Implement cache expiration check
- [ ] Add periodic cleanup of expired entries
- [ ] Make TTL configurable via environment variable

## Phase 4: API Endpoints

### Task 7: Create Rendering API Endpoints

- [ ] Add `/render` endpoint in main.py
- [ ] Accept `url` query parameter
- [ ] Integrate JWT authentication dependency
- [ ] Integrate rendering service
- [ ] Integrate caching layer
- [ ] Return rendered HTML with appropriate headers
- [ ] Add `/health` endpoint for Kubernetes liveness probe
- [ ] Add `/readiness` endpoint for Kubernetes readiness probe

### Task 8: Error Handling & Validation

- [ ] Create Pydantic model for URL validation
- [ ] Validate URL format and scheme (http/https only)
- [ ] Handle render timeout errors gracefully
- [ ] Handle Playwright failures with proper error messages
- [ ] Return appropriate HTTP status codes (400, 403, 500, 503, etc.)
- [ ] Add comprehensive error logging

## Phase 5: Kubernetes Deployment Preparation

### Task 9: Create Dockerfile

- [ ] Create Dockerfile with Python 3.13 base image
- [ ] Install uv package manager
- [ ] Copy and install project dependencies
- [ ] Install Playwright and Firefox browser
- [ ] Configure non-root user for security
- [ ] Optimize image size (multi-stage build if needed)
- [ ] Test Docker build locally

### Task 10: Kubernetes Configuration Files

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

### Task 11: Lifecycle Management

- [ ] Implement graceful shutdown in application
- [ ] Close browser instances on shutdown
- [ ] Configure liveness probe path and settings
- [ ] Configure readiness probe path and settings
- [ ] Test probes locally
- [ ] Add pre-stop hook if needed

## Additional Tasks

### Testing

- [ ] Add unit tests for authentication
- [ ] Add unit tests for cache layer
- [ ] Add integration tests for rendering service
- [ ] Add end-to-end API tests
- [ ] Test with sample JavaScript-heavy websites

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

## Implementation Notes

- **Cache Strategy**: Using Python dict + time module, no external dependencies (Redis)
- **Browser**: Firefox via Playwright
- **Authentication**: JWT with keys from config.py
- **Deployment Target**: Kubernetes
- **Language**: Python 3.13+
- **Framework**: FastAPI with async/await
