# MacroOps AI — Production Deployment Guide

**Target Audience:** DevOps, Operations Engineers, System Administrators  
**System Classification:** Python Flask WSGI Analytical Application + SQLite + Three.js

---

## 1. Production Architecture Overview

In a production environment, MacroOps AI should be deployed behind a production-grade WSGI application server with an Nginx reverse proxy providing TLS termination and static asset caching:

```
[Internet / Clients]
        │ HTTPS (Port 443)
        ▼
   [Nginx Reverse Proxy]
   - Static Asset Caching (/static/*)
   - TLS Termination
   - Rate Limiting
        │ HTTP (Port 5000 or Unix Socket)
        ▼
 [WSGI Server: Waitress / Gunicorn]
   - Multi-Worker Process Pool
   - Pre-loaded Inference Models
        │
   [MacroOps Application (app.py)]
        │
        ├──> macroops_analytics.db (SQLite mode=ro)
        └──> model_artifacts/ (Frozen .joblib models)
```

---

## 2. Prerequisites & Environment Setup

### 2.1 Hardware Recommendations
- **CPU:** 4+ Cores (for parallel LightGBM scoring and concurrent API requests).
- **RAM:** Minimum 8 GB (16 GB recommended for feature caching and multiple worker threads).
- **Disk:** 5 GB SSD storage (accommodates datasets, database, models, and OS logs).

### 2.2 System Packages & Python Environment
Ensure Python 3.10+ is installed:
```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install waitress
```

```bash
# Linux
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## 3. WSGI Server Configuration

### 3.1 Windows Deployment (Waitress)
Create `run_production.py` in the project root:
```python
"""MacroOps AI — Production Entry Point (Waitress WSGI)."""
import os
from waitress import serve
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting MacroOps AI on http://0.0.0.0:{port} via Waitress WSGI...")
    serve(app, host="0.0.0.0", port=port, threads=8)
```
Run with:
```powershell
python run_production.py
```

### 3.2 Linux Deployment (Gunicorn)
Launch Gunicorn with 4 workers and 2 threads per worker:
```bash
gunicorn --workers 4 --threads 2 --bind 127.0.0.1:5000 --timeout 60 app:app
```

---

## 4. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/macroops`:
```nginx
server {
    listen 80;
    server_name macroops.internal;

    # Static Asset Caching
    location /static/ {
        alias /var/www/macroops/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # Application API & Web Views
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
```

---

## 5. Environment Variables & Security Hardening

| Variable | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `production` | Enables production mode |
| `MACROOPS_PORT` | `5000` | Port for WSGI server binding |
| `MACROOPS_DB_PATH` | `/var/www/macroops/macroops_analytics.db` | Absolute path to read-only database |
| `PYTHONUNBUFFERED` | `1` | Ensures real-time stdout log emission |

### File Permission Hardening
```bash
# Make database strictly read-only on disk
chmod 444 macroops_analytics.db

# Restrict model artifacts to read-only
chmod -R 555 model_artifacts/
```

---

## 6. Health & Liveness Checks

Configure automated load balancer health checks to poll:
```
GET http://127.0.0.1:5000/api/health
```
- **Healthy Status:** HTTP 200 with JSON payload `"status": "healthy"`, `"database.connected": true`, `"models.loaded": true`.
- **Degraded Status:** HTTP 503 if database connection fails or models fail to initialize.
