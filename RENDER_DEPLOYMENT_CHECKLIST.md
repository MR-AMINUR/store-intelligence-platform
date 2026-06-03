# Render Deployment Checklist

**Quick Reference** - Use this checklist to ensure smooth deployment to Render.com

---

## ✅ Pre-Deployment (5 minutes)

### 1. Verify Files
- [ ] `Dockerfile` exists in root directory
- [ ] `docker-entrypoint.sh` is executable (`chmod +x docker-entrypoint.sh`)
- [ ] `render.yaml` exists (created ✅)
- [ ] `requirements.txt` is complete
- [ ] `models/yolov8n.pt` is present (6.2 MB)
- [ ] `config/zones.json` exists
- [ ] `init_db.py` exists

### 2. Test Locally
```bash
# Build Docker image
docker build -t store-intelligence-test .

# Run container
docker run -p 8000:8000 store-intelligence-test

# Test health endpoint (in new terminal)
curl http://localhost:8000/health

# Expected: {"status": "healthy", "database": "connected"}
```

### 3. Push to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## 🚀 Deployment Steps (10 minutes)

### Method A: Automatic with Blueprint (Recommended)

1. **Create Render Account**
   - [ ] Go to https://render.com
   - [ ] Sign up (free)
   - [ ] Connect GitHub

2. **Deploy with Blueprint**
   - [ ] Click "New" → "Blueprint"
   - [ ] Select your repository
   - [ ] Render detects `render.yaml`
   - [ ] Click "Apply"

3. **Wait for Build**
   - [ ] Monitor build logs (5-10 minutes)
   - [ ] Build should complete successfully

### Method B: Manual Setup

1. **New Web Service**
   - [ ] Click "New +" → "Web Service"
   - [ ] Connect GitHub repository

2. **Configure**
   ```
   Name: store-intelligence-api
   Environment: Docker
   Region: Oregon
   Branch: main
   Dockerfile Path: ./Dockerfile
   ```

3. **Environment Variables**
   - [ ] Copy from `.env.render` file
   - [ ] Or paste this list:
   ```
   DB_PATH=/app/data/events.db
   LOG_LEVEL=INFO
   YOLO_MODEL_PATH=/app/models/yolov8n.pt
   CONFIDENCE_THRESHOLD=0.5
   TRACKER_MAX_AGE=30
   ZONE_CONFIG_PATH=/app/config/zones.json
   STORE_ID=store_001
   PYTHONUNBUFFERED=1
   PORT=8000
   ```

4. **Disk Storage**
   ```
   Name: store-intelligence-data
   Mount Path: /app/data
   Size: 1 GB
   ```

5. **Create Service**
   - [ ] Click "Create Web Service"
   - [ ] Wait for build

---

## ✅ Verification (2 minutes)

### 1. Check Build Logs
- [ ] No errors in build process
- [ ] "Successfully built" message appears
- [ ] "Deployment successful" message appears

### 2. Test Health Endpoint
```bash
curl https://your-service.onrender.com/health
```
- [ ] Returns `{"status": "healthy", "database": "connected"}`

### 3. Test API Documentation
- [ ] Visit `https://your-service.onrender.com/docs`
- [ ] Swagger UI loads
- [ ] All 7 endpoints visible

### 4. Test API Call
```bash
curl https://your-service.onrender.com/
```
- [ ] Returns API information JSON

### 5. Test Event Ingestion
```bash
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
```
- [ ] Returns `201 Created`

---

## 📋 Required Configuration

### Environment Variables Checklist

- [ ] `DB_PATH` = `/app/data/events.db`
- [ ] `LOG_LEVEL` = `INFO`
- [ ] `YOLO_MODEL_PATH` = `/app/models/yolov8n.pt`
- [ ] `CONFIDENCE_THRESHOLD` = `0.5`
- [ ] `TRACKER_MAX_AGE` = `30`
- [ ] `ZONE_CONFIG_PATH` = `/app/config/zones.json`
- [ ] `STORE_ID` = `store_001`
- [ ] `PYTHONUNBUFFERED` = `1`
- [ ] `PORT` = `8000`

### Dockerfile Configuration Checklist

- [x] Base image: `python:3.10-slim`
- [x] Port exposed: `8000`
- [x] Health check: `/health` endpoint
- [x] Entrypoint: `docker-entrypoint.sh`
- [x] Start command: `uvicorn src.api_server:app --host 0.0.0.0 --port 8000`
- [x] Non-root user: `appuser`
- [x] Working directory: `/app`

### Disk Storage Configuration

- [x] Name: `store-intelligence-data`
- [x] Mount path: `/app/data`
- [x] Size: `1 GB` (free tier)

---

## 🐛 Common Issues & Solutions

### Issue 1: Build Fails

**Symptom**: Build fails with "Dockerfile not found"

**Solution**:
- [ ] Verify Dockerfile is in root directory
- [ ] Check spelling: `Dockerfile` (capital D)
- [ ] Ensure file is committed to git

### Issue 2: Health Check Fails

**Symptom**: "Health check failed" message

**Solution**:
- [ ] Verify `/health` endpoint works locally
- [ ] Check port 8000 is correctly exposed
- [ ] Review startup logs for errors

### Issue 3: Application Won't Start

**Symptom**: Logs show "ModuleNotFoundError" or import errors

**Solution**:
- [ ] Verify all requirements in `requirements.txt`
- [ ] Check Python version compatibility (3.10+)
- [ ] Ensure all source files are in repository

### Issue 4: Model Not Found

**Symptom**: "YOLOv8 model not found" error

**Solution**:
- [ ] Ensure `models/yolov8n.pt` is in repository
- [ ] File size should be ~6.2 MB
- [ ] Check `YOLO_MODEL_PATH` environment variable

### Issue 5: Database Errors

**Symptom**: "Unable to open database file"

**Solution**:
- [ ] Verify disk storage is mounted at `/app/data`
- [ ] Check `DB_PATH` environment variable
- [ ] Ensure `init_db.py` ran successfully (check logs)

---

## 📊 Expected Performance (Free Tier)

- **Build Time**: 5-10 minutes (first build)
- **Startup Time**: 10-20 seconds
- **Health Check**: < 100ms response time
- **API Calls**: 100-500ms response time
- **Sleep**: After 15 minutes of inactivity (free tier only)

---

## 🎯 Success Criteria

Deployment is successful when ALL are true:

- [x] Build completes without errors
- [x] Health endpoint returns 200 OK
- [x] API docs are accessible at `/docs`
- [x] Test API calls succeed
- [x] No errors in runtime logs
- [x] Demo URL is public and shareable

---

## 📝 Your Demo URL

Once deployed, document your URL here:

```
Demo Link: https://__________.onrender.com

Quick Links:
- API Docs:      https://__________.onrender.com/docs
- Health Check:  https://__________.onrender.com/health
- API Info:      https://__________.onrender.com/

Test Commands:
curl https://__________.onrender.com/health
curl https://__________.onrender.com/stores/store_001/metrics
```

---

## ⏱️ Estimated Time

- **Pre-Deployment**: 5 minutes
- **Deployment**: 10 minutes
- **Verification**: 2 minutes
- **Total**: ~17 minutes

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Project Guide**: See `RENDER_DEPLOYMENT_GUIDE.md`
- **Docker Issues**: See `DOCKER_DEPLOYMENT.md`
- **General Setup**: See `README.md`

---

**Checklist Version**: 1.0  
**Last Updated**: 2024-06-03  
**Status**: Ready for Deployment ✅
