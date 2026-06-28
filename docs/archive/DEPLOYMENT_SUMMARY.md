# Complete Deployment Guide - Summary

**Quick reference for deploying both backend and frontend**

---

## 📦 What You're Deploying

### Backend (Render)
- **Technology**: FastAPI + Python 3.11
- **Database**: SQLite (in-memory for free tier)
- **Cost**: FREE
- **Features**: REST API, health monitoring, analytics endpoints

### Frontend (Vercel)
- **Technology**: Next.js 14 + TypeScript + Tailwind CSS
- **Cost**: FREE
- **Features**: Real-time dashboard, charts, auto-refresh

---

## 🚀 Deployment Order

Deploy in this order:

1. **Backend first** (Render) → Get backend URL
2. **Frontend second** (Vercel) → Use backend URL in config

---

## 📋 Backend Deployment (Render)

### Quick Steps

```bash
# 1. Verify backend works locally
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000
# Test: curl http://localhost:8000/health

# 2. Push to GitHub
git add .
git commit -m "Deploy backend to Render"
git push origin main

# 3. Deploy on Render
# Go to: https://dashboard.render.com
# Click: "New +" → "Web Service"
# Connect: Your GitHub repository
# Configure:
#   - Name: store-intelligence-api
#   - Runtime: Python 3
#   - Build Command: pip install -r requirements.txt
#   - Start Command: uvicorn src.api_server:app --host 0.0.0.0 --port $PORT
# Add environment variables (9 total - see render.yaml)
# Click: "Create Web Service"
# Wait: 5-10 minutes

# 4. Get your backend URL
# Copy from Render dashboard: https://store-api-xxxx.onrender.com
```

### Environment Variables (9 required)

| Variable | Value |
|----------|-------|
| `DB_PATH` | `/app/data/events.db` |
| `LOG_LEVEL` | `INFO` |
| `YOLO_MODEL_PATH` | `/app/models/yolov8n.pt` |
| `CONFIDENCE_THRESHOLD` | `0.5` |
| `TRACKER_MAX_AGE` | `30` |
| `ZONE_CONFIG_PATH` | `/app/config/zones.json` |
| `STORE_ID` | `store_001` |
| `PYTHONUNBUFFERED` | `1` |
| `PORT` | `8000` |

**Note**: Copy these from `render.yaml` or `.env.render`

### Verify Backend

```bash
# Test health endpoint
curl https://your-api-xxxx.onrender.com/health
# Expected: {"status":"healthy","checks":{"database":"ok"}}

# Test metrics endpoint
curl https://your-api-xxxx.onrender.com/stores/store_001/metrics
# Expected: JSON with store metrics

# View API documentation
# Open: https://your-api-xxxx.onrender.com/docs
```

**Documentation**: See `render.yaml` and backend README

---

## 🎨 Frontend Deployment (Vercel)

### Quick Steps

```bash
# 1. Test local build
cd frontend
npm run build
# Should see: "Compiled successfully"

# 2. Push to GitHub (if not already done)
git add frontend/
git commit -m "Deploy frontend to Vercel"
git push origin main

# 3. Deploy on Vercel
# Go to: https://vercel.com
# Click: "Add New..." → "Project"
# Import: Your GitHub repository
# Configure:
#   - Root Directory: frontend ⚠️ CRITICAL!
#   - Framework: Next.js (auto-detected)
# Add environment variable:
#   - Key: NEXT_PUBLIC_API_URL
#   - Value: https://your-api-xxxx.onrender.com
#   - Environments: All (Production, Preview, Development)
# Click: "Deploy"
# Wait: 2-3 minutes

# 4. Get your frontend URL
# Copy from Vercel: https://your-project.vercel.app
```

### Environment Variable (1 required)

| Variable | Value | Example |
|----------|-------|---------|
| `NEXT_PUBLIC_API_URL` | Your Render backend URL | `https://store-api-xxxx.onrender.com` |

**⚠️ Important:**
- NO trailing slash!
- Must start with `NEXT_PUBLIC_` (client-side access)
- Use the EXACT URL from Render dashboard

### Verify Frontend

1. **Open dashboard**: https://your-project.vercel.app
2. **Check health**: Top-right should show "Healthy" (green)
3. **Test stores**: Dropdown should have 4 stores
4. **Verify metrics**: Cards should show numbers
5. **Check console**: F12 → Should see no errors
6. **Test mobile**: F12 → Device toolbar → Select phone

**Documentation**: See `VERCEL_DEPLOYMENT_QUICKSTART.md`

---

## 🔗 Complete Deployment URLs

After both deployments:

| Service | URL | Purpose |
|---------|-----|---------|
| **Backend API** | `https://store-api-xxxx.onrender.com` | REST API endpoints |
| **Frontend Dashboard** | `https://your-project.vercel.app` | User interface |
| **API Documentation** | `https://store-api-xxxx.onrender.com/docs` | Swagger UI |
| **Health Check** | `https://store-api-xxxx.onrender.com/health` | API status |

**Save these URLs** for your documentation!

---

## ⏱️ Deployment Timeline

| Step | Time | Action |
|------|------|--------|
| Backend Setup | 5 min | Configure Render service |
| Backend Build | 5-10 min | Install dependencies, start server |
| Backend Verify | 2 min | Test health and metrics endpoints |
| Frontend Setup | 5 min | Configure Vercel project |
| Frontend Build | 2-3 min | Build Next.js application |
| Frontend Verify | 2 min | Test dashboard functionality |
| **Total** | **20-30 min** | First-time deployment |

**Subsequent deployments**: Automatic (git push → auto-deploy in 2-3 min)

---

## ✅ Complete Deployment Checklist

### Backend (Render)

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service created
- [ ] Runtime set to Python 3
- [ ] Build command configured
- [ ] Start command configured
- [ ] 9 environment variables added
- [ ] Build completed successfully
- [ ] Health endpoint returns 200
- [ ] Metrics endpoint returns data
- [ ] Backend URL saved

### Frontend (Vercel)

- [ ] Backend URL obtained from Render
- [ ] Local build tested (`npm run build`)
- [ ] Code pushed to GitHub
- [ ] Vercel account created
- [ ] Project imported from GitHub
- [ ] Root directory set to `frontend`
- [ ] Environment variable added
- [ ] Build completed successfully
- [ ] Dashboard loads without errors
- [ ] Health indicator shows "Healthy"
- [ ] All stores in dropdown (4 stores)
- [ ] Metrics display correctly
- [ ] Charts render properly
- [ ] No console errors (F12)
- [ ] Mobile responsive (tested)
- [ ] Frontend URL saved

### Documentation

- [ ] Backend URL documented
- [ ] Frontend URL documented
- [ ] Environment variables documented
- [ ] Test instructions prepared
- [ ] Screenshots taken (optional)
- [ ] Submission materials ready

---

## 🐛 Common Issues & Solutions

### Backend Issues

**Issue**: Build fails on Render
- **Solution**: Check `requirements.txt` and Python version (3.11)
- **Fix**: Test locally first: `pip install -r requirements.txt`

**Issue**: Health endpoint returns 503
- **Solution**: Check environment variables, especially `DB_PATH`
- **Fix**: Verify all 9 variables are set correctly

**Issue**: Database errors
- **Solution**: Free tier uses in-memory database (data lost on restart)
- **Note**: This is expected behavior for free tier

### Frontend Issues

**Issue**: Dashboard shows "Failed to fetch data"
- **Solution**: Check `NEXT_PUBLIC_API_URL` in Vercel settings
- **Fix**: Verify no trailing slash, use exact Render URL

**Issue**: 404 Page Not Found
- **Solution**: Root directory not set correctly
- **Fix**: Vercel → Settings → Root Directory → `frontend`

**Issue**: Health shows "Unhealthy"
- **Solution**: Backend might be sleeping (free tier)
- **Fix**: Wait 60 seconds, refresh page (cold start)

**Issue**: Styles not loading
- **Solution**: Build issue
- **Fix**: Test locally: `npm run build`, fix errors, redeploy

---

## 🔄 Continuous Deployment

Both platforms support automatic deployments:

```bash
# Make changes to your code
vim src/api_server.py              # Backend change
vim frontend/src/components/Dashboard.tsx  # Frontend change

# Commit and push
git add .
git commit -m "Update feature X"
git push origin main

# Automatic deployment
# Render: Rebuilds backend (5-10 min)
# Vercel: Rebuilds frontend (2-3 min)
```

**No manual steps needed!** Both services auto-deploy on git push.

---

## 💰 Cost Breakdown

### Free Tier Limits

**Render Free Tier:**
- ✅ 750 hours/month (enough for 24/7)
- ✅ 512 MB RAM
- ⚠️  Sleeps after 15 min inactivity
- ⚠️  Cold start: 30-60 seconds
- ⚠️  No persistent disk (in-memory database)

**Vercel Hobby Tier:**
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ 1 TB total storage
- ✅ No sleep/cold starts
- ✅ Global CDN
- ✅ Automatic HTTPS

**Total Cost: $0/month** for both! 🎉

---

## 📊 Performance Expectations

### Backend (Render)
- **First request after sleep**: 30-60 seconds (cold start)
- **Subsequent requests**: 100-500ms
- **Health check**: 50-200ms
- **Metrics query**: 200-800ms

### Frontend (Vercel)
- **First page load**: 1-2 seconds
- **Return visits**: 200-500ms (cached)
- **API calls**: Depends on backend response time
- **Global CDN**: Fast worldwide delivery

---

## 🎯 For Purplle/Interview Submission

### Include in Documentation

```
# Store Intelligence Platform - Live Demo

## Deployment URLs
- **Frontend Dashboard**: https://your-project.vercel.app
- **Backend API**: https://your-api-xxxx.onrender.com
- **API Documentation**: https://your-api-xxxx.onrender.com/docs

## Tech Stack
- **Backend**: FastAPI + Python 3.11 + SQLite
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Deployment**: Render (Backend) + Vercel (Frontend)
- **Database**: SQLite (in-memory for demo)

## Features Demonstrated
✅ Real-time store metrics (entries, exits, occupancy, visit duration)
✅ Conversion funnel analysis with 4 stages
✅ Anomaly detection (crowd surge, queue abandonment, unusual patterns)
✅ Multi-store support (4 stores with test data)
✅ Health monitoring dashboard
✅ Auto-refresh every 30 seconds
✅ Responsive design (mobile/tablet/desktop)
✅ RESTful API with OpenAPI documentation

## Test Instructions
1. Open dashboard: https://your-project.vercel.app
2. Verify health indicator shows "Healthy" (top-right)
3. Select different stores from sidebar (store_001, store_002, store_1, store_2)
4. View metrics cards update with store data
5. Check conversion funnel visualization
6. Wait 30 seconds to see auto-refresh
7. Test API directly: https://your-api-xxxx.onrender.com/docs

## Known Limitations
- Free tier backend sleeps after 15 min (first request takes 30-60s)
- In-memory database (data resets on backend restart)
- Limited to 750 server hours/month (sufficient for demo)

## Architecture Highlights
- Event-driven architecture with idempotent operations
- Property-based testing for correctness validation
- Structured logging with correlation IDs
- Comprehensive error handling and retry logic
- CORS-enabled for cross-origin requests
```

---

## 📚 All Documentation Files

**Backend Deployment:**
- `render.yaml` - Render configuration
- `.env.render` - Environment variables template
- `Dockerfile` - Container configuration

**Frontend Deployment:**
- `frontend/VERCEL_DEPLOY.txt` - Quick checklist
- `frontend/VERCEL_STEP_BY_STEP.md` - Visual guide with screenshots
- `VERCEL_DEPLOYMENT_QUICKSTART.md` - Detailed walkthrough
- `frontend/DEPLOYMENT.md` - Complete deployment guide

**Connection & Troubleshooting:**
- `FRONTEND_BACKEND_FINAL_FIX.md` - Connection fix guide
- `CONNECTION_STATUS_SUMMARY.md` - Status summary
- `DEPLOYMENT_SUMMARY.md` - This file

---

## 🆘 Getting Help

### Render Support
- Documentation: https://render.com/docs
- Status: https://status.render.com
- Community: https://community.render.com

### Vercel Support
- Documentation: https://vercel.com/docs
- Status: https://vercel-status.com
- Community: https://github.com/vercel/next.js/discussions

---

## ✨ Success!

When both deployments are complete:

✅ **Backend**: Live API serving requests  
✅ **Frontend**: Live dashboard displaying data  
✅ **Auto-deploy**: Future updates deploy automatically  
✅ **HTTPS**: Secure connections for both services  
✅ **Global**: Fast delivery worldwide via CDN  
✅ **Free**: $0/month for both services  

**You're ready to share your project!** 🎊

---

**Last Updated**: 2024-06-27  
**Deployment Guide Version**: 1.0  
**Total Deployment Time**: 20-30 minutes
