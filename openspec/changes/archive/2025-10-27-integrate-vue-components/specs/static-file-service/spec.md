# Static File Service Specification

**Spec ID**: `static-file-service`
**Change ID**: `integrate-vue-components`
**Version**: 1.0
**Status**: DRAFT

---

## Overview

This specification defines the configuration and operation of the static file service for the Vue-integrated CODEX Trading Dashboard, enabling proper serving of Vue components, JavaScript modules, CSS files, and other static assets.

---

## Requirements

### Functional Requirements

#### FR-001: Static File Serving
- **Description**: Serve static files from designated directory
- **Priority**: P0
- **Acceptance Criteria**:
  - All static files accessible via HTTP
  - Correct MIME types returned
  - No 404 errors for valid paths
  - Files served from `/static` URL path

#### FR-002: Directory Structure Support
- **Description**: Support nested directory structure
- **Priority**: P0
- **Directory Layout**:
  ```
  static/
  ├── js/
  │   ├── components/     # Vue components
  │   ├── stores/         # Pinia stores
  │   ├── router/         # Router config
  │   └── utils/          # Utility functions
  ├── css/
  │   ├── main.css        # Global styles
  │   └── components.css  # Component styles
  └── assets/
      ├── images/
      └── fonts/
  ```
- **Acceptance Criteria**:
  - All subdirectories accessible
  - Files load from correct paths
  - No path traversal vulnerabilities

#### FR-001: CORS Configuration
- **Description**: Enable CORS for static file requests
- **Priority**: P0
- **Acceptance Criteria**:
  - CORS headers present on all responses
  - Allow requests from any origin (*)
  - Support common HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
  - Allow all headers

---

## Technical Specifications

### FastAPI StaticFiles Configuration

#### Code Implementation

```python
# In run_dashboard.py
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

# =============================================================================
# STATIC FILE SERVICE CONFIGURATION
# =============================================================================

# Create static directory path
static_dir = project_root / "src" / "dashboard" / "static"

# Ensure static directory exists
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created static directory: {static_dir}")

# Create subdirectories
subdirs = ['js', 'js/components', 'js/stores', 'js/router', 'js/utils', 'css', 'assets', 'assets/images', 'assets/fonts']
for subdir in subdirs:
    (static_dir / subdir).mkdir(parents=True, exist_ok=True)

# =============================================================================
# MOUNT STATIC FILE SERVICES
# =============================================================================

# Mount static files at /static
app.mount(
    "/static",
    StaticFiles(directory=str(static_dir)),
    name="static"
)

# Mount JavaScript files at /static/js
app.mount(
    "/static/js",
    StaticFiles(directory=str(static_dir / "js")),
    name="static-js"
)

# Mount CSS files at /static/css
app.mount(
    "/static/css",
    StaticFiles(directory=str(static_dir / "css")),
    name="static-css"
)

# Mount assets at /static/assets
app.mount(
    "/static/assets",
    StaticFiles(directory=str(static_dir / "assets")),
    name="static-assets"
)

print(f"✅ Static file services mounted at /static/*")
```

### CORS Middleware Configuration

```python
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Allow all origins (for development; restrict in production)
    allow_origins=["*"],

    # Allow credentials in requests
    allow_credentials=True,

    # Allow all HTTP methods
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],

    # Allow all headers
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRFToken",
        "Cache-Control"
    ],

    # Expose headers to client
    expose_headers=[
        "Content-Length",
        "Content-Type",
        "Cache-Control",
        "Last-Modified"
    ],

    # Cache preflight requests for 1 hour
    max_age=3600
)

print(f"✅ CORS middleware configured")
```

### File Type Mappings

```python
# FastAPI automatically handles MIME types, but we can extend if needed
MIME_TYPE_MAPPING = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".eot": "application/vnd.ms-fontobject",
    ".otf": "font/otf",
    ".map": "application/json"
}
```

---

## Directory Structure Specification

### Static Directory Layout

```
src/dashboard/static/
│
├── js/                          # JavaScript files
│   ├── components/              # Vue components
│   │   ├── BacktestPanel.js
│   │   ├── BacktestForm.js
│   │   ├── BacktestResults.js
│   │   ├── AgentPanel.js
│   │   ├── AgentList.js
│   │   ├── AgentStatus.js
│   │   ├── AgentControl.js
│   │   ├── AgentLogs.js
│   │   ├── RiskPanel.js
│   │   ├── PortfolioRisk.js
│   │   ├── VaRChart.js
│   │   ├── PositionRisk.js
│   │   ├── AlertManager.js
│   │   ├── RiskHeatmap.js
│   │   ├── TradingPanel.js
│   │   ├── OrderForm.js
│   │   ├── PositionTable.js
│   │   ├── TradeHistory.js
│   │   └── RealTimeTicker.js
│   │
│   ├── stores/                  # Pinia stores
│   │   ├── agents.js
│   │   ├── portfolio.js
│   │   ├── risk.js
│   │   ├── backtest.js
│   │   ├── trading.js
│   │   └── index.js
│   │
│   ├── router/                  # Vue Router config
│   │   └── index.js
│   │
│   ├── utils/                   # Utility functions
│   │   ├── httpClient.js
│   │   ├── websocket.js
│   │   ├── formatters.js
│   │   ├── validators.js
│   │   └── logger.js
│   │
│   ├── main.js                  # Main application entry
│   ├── app.js                   # App configuration
│   └── vendor.js                # Vendor libraries (if needed)
│
├── css/                         # Stylesheets
│   ├── main.css                 # Global styles
│   ├── components.css           # Component-specific styles
│   ├── themes.css               # Theme definitions
│   └── responsive.css           # Responsive breakpoints
│
├── assets/                      # Static assets
│   ├── images/                  # Images
│   │   ├── logo.png
│   │   ├── icons/
│   │   └── backgrounds/
│   │
│   └── fonts/                   # Font files
│       ├── inter-regular.woff2
│       ├── inter-medium.woff2
│       └── inter-bold.woff2
│
└── index.html                   # Entry HTML file (optional, can be in templates/)
```

### File Naming Conventions

#### JavaScript Files
- **Components**: PascalCase, e.g., `AgentPanel.js`
- **Stores**: camelCase with `use` prefix, e.g., `useAgentStore.js`
- **Utils**: camelCase, e.g., `httpClient.js`
- **Router**: lowercase, e.g., `index.js`

#### CSS Files
- **Global**: lowercase, e.g., `main.css`
- **Components**: hyphenated, e.g., `agent-panel.css`
- **Themes**: descriptive, e.g., `dark-theme.css`

#### Assets
- **Images**: lowercase with hyphens, e.g., `logo-trading.png`
- **Icons**: prefixed with `icon-`, e.g., `icon-agent.svg`
- **Fonts**: format-version, e.g., `inter-regular.woff2`

---

## URL Mapping Specification

### Static File URLs

| Local Path | URL | Example |
|------------|-----|---------|
| `static/js/main.js` | `/static/js/main.js` | `http://localhost:8001/static/js/main.js` |
| `static/js/components/AgentPanel.js` | `/static/js/components/AgentPanel.js` | `http://localhost:8001/static/js/components/AgentPanel.js` |
| `static/css/main.css` | `/static/css/main.css` | `http://localhost:8001/static/css/main.css` |
| `static/assets/images/logo.png` | `/static/assets/images/logo.png` | `http://localhost:8001/static/assets/images/logo.png` |

### Access Patterns

```html
<!-- In index.html -->
<script src="/static/js/main.js"></script>
<script src="/static/js/app.js"></script>
<link rel="stylesheet" href="/static/css/main.css">

<!-- Component references -->
<img src="/static/assets/images/logo.png" alt="Logo">
```

---

## Caching Strategy

### Cache Headers Configuration

```python
from fastapi import Request, Response
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta

# Custom static file handler with caching
async def serve_static_with_cache(request: Request, path: str):
    file_path = static_dir / path

    if not file_path.exists():
        return Response(status_code=404)

    # Determine cache headers based on file type
    if path.endswith(('.js', '.css')):
        # Cache JS/CSS for 1 day
        cache_control = "public, max-age=86400"
    elif path.endswith(('.woff', '.woff2', '.ttf')):
        # Cache fonts for 1 year
        cache_control = "public, max-age=31536000"
    elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
        # Cache images for 1 week
        cache_control = "public, max-age=604800"
    else:
        # Default: no cache
        cache_control = "no-cache"

    return FileResponse(
        path=file_path,
        headers={
            "Cache-Control": cache_control,
            "X-Content-Type-Options": "nosniff"
        }
    )
```

### Cache Invalidation

**Strategy**: Use versioned filenames for cache-busting

```javascript
// Before build
<script src="/static/js/app.js"></script>

// After build (with version hash)
<script src="/static/js/app.v1.2.3.js"></script>

// Or use query string
<script src="/static/js/app.js?v=1.2.3"></script>
```

---

## Security Requirements

### Path Traversal Prevention

```python
# Ensure safe file paths
import os

def secure_path_join(base: Path, *paths: str) -> Path:
    """Join paths and resolve to ensure no directory traversal"""
    final_path = base.joinpath(*paths).resolve()

    # Ensure path is within base directory
    if not str(final_path).startswith(str(base.resolve())):
        raise ValueError(f"Path traversal attempt: {paths}")

    return final_path
```

### File Type Validation

```python
ALLOWED_EXTENSIONS = {
    '.js', '.css', '.json', '.html',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.woff', '.woff2', '.ttf', '.eot', '.otf'
}

def validate_file_extension(file_path: Path) -> bool:
    """Validate file extension is allowed"""
    return file_path.suffix.lower() in ALLOWED_EXTENSIONS
```

### Content Security Policy (CSP)

```python
# Add CSP headers
app.add_middleware(
    CORSMiddleware,
    # ... other settings
)

# Add CSP response header
@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-eval' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "connect-src 'self' ws: wss:;"
    )
    return response
```

---

## Performance Requirements

### File Serving Performance

- **Small files (< 10 KB)**: < 10ms
- **Medium files (10-100 KB)**: < 50ms
- **Large files (> 100 KB)**: < 200ms

### Compression

```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Compress files > 1KB
    compresslevel=6     # Compression level (1-9)
)
```

### CDN Support (Future)

```python
# For production deployment
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "")

def get_cdn_url(path: str) -> str:
    """Get CDN URL if configured, otherwise local URL"""
    if CDN_BASE_URL:
        return f"{CDN_BASE_URL}/static/{path}"
    return f"/static/{path}"
```

---

## Error Handling

### 404 Handling

```python
@app.get("/static/{path:path}")
async def serve_static_file(path: str):
    """Serve static files with proper error handling"""
    try:
        file_path = static_dir / path

        if not file_path.exists():
            raise FileNotFoundError(f"Static file not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        return FileResponse(
            path=file_path,
            media_type=get_media_type(file_path.suffix)
        )

    except FileNotFoundError:
        logger.warning(f"Static file not found: {path}")
        return JSONResponse(
            status_code=404,
            content={"error": "File not found", "path": path}
        )

    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
```

### Media Type Detection

```python
import mimetypes

def get_media_type(extension: str) -> str:
    """Get MIME type for file extension"""
    mime_type, _ = mimetypes.guess_type(f"dummy{extension}")
    return mime_type or "application/octet-stream"
```

---

## Monitoring & Logging

### Access Logging

```python
import logging

logger = logging.getLogger("static_files")

@app.middleware("http")
async def log_static_requests(request: Request, call_next):
    """Log all static file requests"""
    if request.url.path.startswith("/static/"):
        logger.info(
            f"Static file request: {request.method} {request.url.path} - "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )
    return await call_next(request)
```

### Metrics Collection

```python
# Track file serving metrics
metrics = {
    'requests_total': 0,
    'requests_by_type': {},
    'response_time_avg': 0,
    '404_errors': 0
}

@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # Update metrics
    metrics['requests_total'] += 1
    response_time = time.time() - start_time
    metrics['response_time_avg'] = (metrics['response_time_avg'] + response_time) / 2

    if response.status_code == 404:
        metrics['404_errors'] += 1

    return response
```

---

## Deployment Considerations

### Development vs Production

```python
import os

# Determine environment
ENV = os.getenv("ENV", "development")

if ENV == "development":
    # Development: Enable hot reload, detailed errors
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    # Enable debug middleware
else:
    # Production: Optimize for performance
    # Use CDN for static files
    # Enable compression
    # Set aggressive caching
    pass
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy static files
COPY src/dashboard/static/ /app/src/dashboard/static/

# Copy application
COPY . /app/

EXPOSE 8001

CMD ["python", "run_dashboard.py"]
```

### Nginx Configuration (for production)

```nginx
server {
    listen 80;
    server_name localhost;

    # Serve static files with Nginx
    location /static/ {
        alias /app/src/dashboard/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    # Proxy API requests to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Testing Requirements

### Unit Tests

```python
# test_static_files.py
from fastapi.testclient import TestClient
from run_dashboard import app

client = TestClient(app)

def test_static_file_exists():
    """Test that static files are served"""
    response = client.get("/static/js/main.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]

def test_static_file_not_found():
    """Test 404 for non-existent files"""
    response = client.get("/static/js/nonexistent.js")
    assert response.status_code == 404

def test_cors_headers():
    """Test CORS headers are present"""
    response = client.get("/static/css/main.css")
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"

def test_cache_headers():
    """Test cache headers for different file types"""
    js_response = client.get("/static/js/main.js")
    assert "cache-control" in js_response.headers

    img_response = client.get("/static/assets/images/logo.png")
    assert "cache-control" in img_response.headers
```

### Integration Tests

```python
def test_static_files_in_html():
    """Test that HTML can load static files"""
    response = client.get("/")
    assert response.status_code == 200

    # Check that HTML references static files
    html = response.text
    assert "/static/js/" in html
    assert "/static/css/" in html
```

---

## Acceptance Criteria

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-001 | Static File Serving | P0 | - |
| FR-002 | Directory Structure Support | P0 | - |
| FR-003 | CORS Configuration | P0 | - |
| SEC-001 | Path Traversal Prevention | P0 | - |
| SEC-002 | File Type Validation | P0 | - |
| PERF-001 | File Serving Performance | P1 | - |
| PERF-002 | Compression Support | P1 | - |
| MON-001 | Access Logging | P2 | - |
| TEST-001 | Unit Test Coverage | P1 | - |

---

**Spec Status**: DRAFT
**Review Date**: TBD
**Approved By**: TBD
