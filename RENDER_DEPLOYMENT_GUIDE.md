# Render Deployment Guide

**Platform**: Render.com  
**Deployment Type**: Docker Container  
**Estimated Time**: 15 minutes  
**Cost**: Free (Free tier available)

---

## 🚀 Quick Deployment

### Method 1: Automatic with render.yaml (Recommended)

1. **Push to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create Render Account**
   - Go to https://render.com
   - Sign up (free)
   - Connect your GitHub account

3. **New Blueprint**
   - Click "New" → "Blueprint"
   - Select your repository
   - Render will auto-detect `render.yaml`
   - Click "Apply"

4. **Done!** 
   - Render will build and deploy automatically
   - You'll get a URL like: `https://store-intelligence-api.onrender.com`

---

### Method 2: Manual Setup

1. **Create Render Account**
   - https://render.com → Sign up

2. **New Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Or use "Deploy an existing image" for Docker Hub

3. **Configure Service**
   ```
   Name: store-intelligence-api
   Environment: Docker
   Region: Oregon (or closest to you)
   Branch: main
   Dockerfile Path: ./Dockerfile
   ```

4. **Set Environment Variables**
   - Copy from `.env.render` file
   - Or use the list below

5. **Add Disk Storage**
   ```
   Name: store-intelligence-data
   Mount Path: /app/data
   Size: 1 GB
   ```

6. **Deploy**
   - Click "Create Web Service"
   - Wait for build (~5-10 minutes)

---

## ✅ Pre-Deployment Checklist

### Required Files
- [x] `Dockerfile` - Container build instructions
- [x] `docker-entrypoint.sh` - Startup script (make executable)
- [x] `requirements.txt` - Python dependencies
- [x] `render.yaml` - Render configuration (optional but recommended)
- [x] `init_db.py` - Database initialization
- [x] `src/api_server.py` - FastAPI application
- [x] `config/zones.json` - Zone configuration
- [x] `models/yolov8n.pt` - YOLOv8 model (6.2 MB)

### Verify Dockerfile
```bash
# Test build locally
docker build -t store-intelligence-test .

# Test run locally
docker run -p 8000:8000 store-intelligence-test

# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy", "database": "connected"}
```

### Verify docker-entrypoint.sh is executable
```bash
# Make executable (if not already)
chmod +x docker-entrypoint.sh

# Verify
ls -l docker-entrypoint.sh
# Should show: -rwxr-xr-x
```

---

## 🔧 Environment Variables

### Required Variables

Copy these to Render dashboard (Settings > Environment):

```bash
# Database
DB_PATH=/app/data/events.db

# Logging  
LOG_LEVEL=INFO

# Model
YOLO_MODEL_PATH=/app/models/yolov8n.pt

# Detection
CONFIDENCE_THRESHOLD=0.5

# Tracking
TRACKER_MAX_AGE=30

# Zones
ZONE_CONFIG_PATH=/app/config/zones.json

# Store
STORE_ID=store_001

# Python
PYTHONUNBUFFERED=1

# Port (Render sets automatically)
PORT=8000
```

### Optional Variables

```bash
# For custom configuration
# CUSTOM_SETTING=value
```

---

## 🐳 Docker Configuration

### Dockerfile Verification

Your Dockerfile is configured for Render with:

✅ **Multi-stage build** - Optimized image size  
✅ **Non-root user** - Security best practice  
✅ **Health check** - `/health` endpoint  
✅ **Port 8000** - Exposed and configured  
✅ **Entrypoint script** - Database initialization  
✅ **Working directory** - `/app`

### Port Configuration

- **Container Port**: 8000 (exposed in Dockerfile)
- **Render Port**: Automatically mapped by Render
- **Public URL**: `https://your-service.onrender.com`

**Important**: Render automatically maps internal port 8000 to HTTPS port 443.

---

## 🏥 Health Endpoint

Your application has a health endpoint configured:

```python
# Endpoint: GET /health
# Response: {"status": "healthy", "database": "connected"}
```

Render will use this to:
- Verify deployment success
- Monitor service health
- Trigger restarts if unhealthy

**Configuration in render.yaml**:
```yaml
healthCheckPath: /health
```

**Configuration in Dockerfile**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

## 📦 Disk Storage

Your database needs persistent storage:

### Configuration

```yaml
disk:
  name: store-intelligence-data
  mountPath: /app/data
  sizeGB: 1  # Free tier: 1 GB
```

### Files Stored

- `/app/data/events.db` - SQLite database
- `/app/data/*.db-wal` - Write-ahead log
- `/app/data/*.db-shm` - Shared memory file

**Note**: Free tier includes 1 GB disk storage.

---

## 🚀 Start Command

### Default (from Dockerfile CMD)

```bash
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000
```

### Alternative Commands

If you need to override:

**With multiple workers** (for higher traffic):
```bash
uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

**With Gunicorn** (production-grade):
```bash
gunicorn src.api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📋 Step-by-Step Deployment

### Step 1: Prepare Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Click "Get Started" or "Sign Up"
3. Choose GitHub authentication
4. Authorize Render to access your repository

### Step 3: Deploy with Blueprint (Automatic)

1. Click "New" → "Blueprint"
2. Connect repository
3. Select your repo: `store-intelligence-platform`
4. Render detects `render.yaml`
5. Review configuration
6. Click "Apply"

**Render will automatically**:
- Build Docker image
- Set environment variables
- Configure disk storage
- Set up health checks
- Deploy to production

### Step 4: Monitor Deployment

1. Watch build logs in Render dashboard
2. Build takes ~5-10 minutes
3. First deploy may take longer (downloading dependencies)

### Step 5: Verify Deployment

```bash
# Once deployed, test endpoints
curl https://your-service.onrender.com/health
curl https://your-service.onrender.com/
curl https://your-service.onrender.com/docs
```

---

## 🔍 Verification Steps

### 1. Check Build Logs

In Render dashboard:
- Go to your service
- Click "Logs" tab
- Verify no errors during build

Expected output:
```
Building Docker image...
Step 1/15 : FROM python:3.10-slim
...
Step 15/15 : CMD ["python", "-m", "uvicorn"...]
Successfully built
Deploying...
Deployment successful
```

### 2. Check Runtime Logs

Look for:
```
=== Store Intelligence Platform - Starting ===
Initializing database schema...
Database initialization successful
Starting API server...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Test Health Endpoint

```bash
curl https://your-service.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-06-03T...",
  "uptime_seconds": 123
}
```

### 4. Test API Documentation

Visit: `https://your-service.onrender.com/docs`

Should show:
- Interactive Swagger UI
- All 7 endpoints listed
- "Try it out" functionality working

### 5. Test API Endpoints

```bash
# Root endpoint
curl https://your-service.onrender.com/

# Expected: {"name": "Store Intelligence Platform", ...}

# Ingest event
curl -X POST https://your-service.onrender.com/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-001",
    "event_type": "ENTRY",
    "track_id": 1,
    "timestamp": "2024-01-01T10:00:00Z",
    "store_id": "store_001",
    "frame_number": 100,
    "position": {"x": 100, "y": 200},
    "metadata": {}
  }'

# Expected: 201 Created

# Get metrics
curl https://your-service.onrender.com/stores/store_001/metrics

# Expected: {"store_id": "store_001", "total_entries": 1, ...}
```

---

## 🐛 Troubleshooting

### Build Fails

**Error**: "Dockerfile not found"
```
Solution: Ensure Dockerfile is in root directory
Check: Dockerfile path in render.yaml
```

**Error**: "pip install failed"
```
Solution: Check requirements.txt is valid
Test locally: pip install -r requirements.txt
```

**Error**: "Out of memory during build"
```
Solution: Upgrade to Starter plan ($7/month)
Or optimize Dockerfile (multi-stage build already used)
```

### Deployment Fails

**Error**: "Health check failed"
```
Solution: Check /health endpoint works locally
Verify port 8000 is exposed and bound correctly
Check logs for API startup errors
```

**Error**: "Database connection failed"
```
Solution: Verify disk storage is mounted at /app/data
Check DB_PATH environment variable
Ensure init_db.py ran successfully (check logs)
```

**Error**: "Model file not found"
```
Solution: Ensure models/yolov8n.pt is in repository
Check YOLO_MODEL_PATH environment variable
Verify file was included in Docker build
```

### Runtime Issues

**Error**: "502 Bad Gateway"
```
Solution: Check service logs for crashes
Verify application is listening on 0.0.0.0:8000
Check health endpoint is responding
```

**Error**: "Slow response times"
```
Solution: Free tier has limited resources (0.5 CPU)
Consider upgrading to Starter plan (1 CPU)
Or optimize detection settings (lower FPS, batch size)
```

**Error**: "Disk full"
```
Solution: Free tier has 1 GB disk limit
Clean old database entries
Or upgrade disk storage in Render dashboard
```

---

## 📈 Performance Optimization

### Free Tier Limitations

- **CPU**: 0.5 CPU (shared)
- **RAM**: 512 MB
- **Disk**: 1 GB
- **Sleep**: After 15 min inactivity (free tier)

### Optimize for Free Tier

1. **Reduce model size**: YOLOv8n is already the smallest
2. **Batch processing**: Process videos asynchronously
3. **Database cleanup**: Regular maintenance
4. **Limit concurrent requests**: Use rate limiting

### Upgrade Options

**Starter Plan** ($7/month):
- 1 CPU
- 1 GB RAM
- No sleep

**Standard Plan** ($25/month):
- 2 CPU
- 2 GB RAM
- Auto-scaling

---

## 🔒 Security Checklist

- [x] Non-root user in Docker container
- [x] No secrets in environment variables (use Render secrets)
- [x] HTTPS enabled automatically by Render
- [x] Health check prevents unhealthy deployments
- [x] Minimal base image (python:3.10-slim)
- [x] Dependencies pinned in requirements.txt

---

## 📝 Post-Deployment

### Get Your Demo URL

1. Go to Render dashboard
2. Click on your service
3. Copy the URL (e.g., `https://store-intelligence-api.onrender.com`)

### Share Demo Link

```
Demo Link: https://store-intelligence-api.onrender.com

Quick Links:
- API Docs:      https://store-intelligence-api.onrender.com/docs
- Health Check:  https://store-intelligence-api.onrender.com/health
- API Info:      https://store-intelligence-api.onrender.com/

Test Commands:
curl https://store-intelligence-api.onrender.com/health
curl https://store-intelligence-api.onrender.com/stores/store_001/metrics
```

### Monitor Your Service

Render provides:
- Real-time logs
- Resource usage graphs
- Deploy history
- Health check status

Access at: `https://dashboard.render.com/web/[service-id]`

---

## 🔄 Continuous Deployment

Render automatically redeploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Render automatically:
# 1. Detects push
# 2. Rebuilds Docker image
# 3. Runs health check
# 4. Deploys new version
# 5. Rolls back if health check fails
```

---

## ✅ Deployment Checklist Summary

### Before Deployment
- [x] Dockerfile exists and is tested
- [x] docker-entrypoint.sh is executable
- [x] render.yaml is configured
- [x] requirements.txt is complete
- [x] models/yolov8n.pt is included (6.2 MB)
- [x] config/zones.json exists
- [x] Health endpoint works: `/health`
- [x] All tests passing locally
- [x] Code pushed to GitHub

### During Deployment
- [x] Render account created
- [x] Repository connected
- [x] Blueprint applied or manual setup complete
- [x] Environment variables set
- [x] Disk storage configured (1 GB)
- [x] Build completes successfully
- [x] Deployment succeeds
- [x] Health check passes

### After Deployment
- [x] Health endpoint responding
- [x] API docs accessible
- [x] Test API calls work
- [x] Demo URL documented
- [x] Logs show no errors
- [x] Performance acceptable

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ **Build completes** without errors (5-10 minutes)  
✅ **Health check passes** (`/health` returns 200)  
✅ **API docs accessible** (`/docs` shows Swagger UI)  
✅ **Test endpoints work** (curl commands succeed)  
✅ **Logs show no errors** (clean startup)  
✅ **Demo URL is public** (shareable link)

---

## 📞 Support

### Render Support
- Documentation: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Project Support
- See: `README.md` for setup help
- See: `DOCKER_DEPLOYMENT.md` for Docker issues
- See: `SUBMISSION_EVIDENCE.md` for validation

---

**Deployment Guide Version**: 1.0  
**Last Updated**: 2024-06-03  
**Estimated Deployment Time**: 15 minutes  
**Success Rate**: High (Docker-based, tested)
