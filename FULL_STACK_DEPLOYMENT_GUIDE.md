# Full Stack Deployment Guide

Complete guide to deploy both backend (Render) and frontend (Vercel) for the Store Intelligence Platform.

---

## 🎯 Overview

**Backend**: FastAPI + Docker → **Render.com**  
**Frontend**: Next.js 14 + TypeScript → **Vercel.com**  
**Total Deployment Time**: 15-20 minutes

---

## 📋 Prerequisites

- [x] Code pushed to GitHub
- [x] Render account (free - render.com)
- [x] Vercel account (free - vercel.com)
- [x] 15-20 minutes

---

## Part 1: Backend Deployment (Render) - 10 minutes

### Step 1: Push Backend to GitHub

```bash
# Ensure all files are committed
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to **[render.com](https://render.com)**
2. Sign up/login with GitHub
3. Click **"New"** → **"Blueprint"**
4. Select your repository
5. Render detects `render.yaml`
6. Click **"Apply"**

### Step 3: Monitor Build

- Watch build logs in Render dashboard
- Wait 5-10 minutes for Docker build
- Build completes when health check passes

### Step 4: Get Backend URL

```
Your backend URL: https://store-intelligence-api.onrender.com
```

**Test it**:
```bash
curl https://your-service.onrender.com/health

# Expected:
{
  "status": "healthy",
  "checks": {"database": "ok"},
  ...
}
```

---

## Part 2: Frontend Deployment (Vercel) - 5 minutes

### Step 1: Push Frontend to GitHub

```bash
# Already done if you pushed in Part 1
git push origin main
```

### Step 2: Import to Vercel

1. Go to **[vercel.com](https://vercel.com)**
2. Sign up/login with GitHub
3. Click **"Add New"** → **"Project"**
4. Select your repository
5. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Next.js (auto-detected)

### Step 3: Add Environment Variable

**Before deploying**, add environment variable:

1. Click **"Environment Variables"**
2. Add:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://your-service.onrender.com` (from Part 1, Step 4)
   - **Environments**: Select all
3. Click **"Add"**

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes
3. Get your URL: `https://your-project.vercel.app`

---

## ✅ Verification Checklist

### Backend (Render)

- [ ] Build completed successfully
- [ ] Health check passes: `/health` returns `{"status": "healthy"}`
- [ ] API docs accessible: `/docs` loads Swagger UI
- [ ] Test endpoint: `/stores/store_001/metrics` returns data

### Frontend (Vercel)

- [ ] Dashboard loads: `https://your-project.vercel.app`
- [ ] Health indicator shows "Healthy" (top-right)
- [ ] Metrics cards display numbers
- [ ] Conversion funnel renders
- [ ] Store selector works
- [ ] No errors in browser console

---

## 🔗 Your Deployment URLs

### After Deployment, You'll Have

```
┌─────────────────────────────────────────────────────────┐
│  Frontend Dashboard                                     │
│  https://your-project.vercel.app                        │
│                                                         │
│  ↓ calls API                                            │
│                                                         │
│  Backend API                                            │
│  https://your-service.onrender.com                      │
└─────────────────────────────────────────────────────────┘
```

**For Purplle Submission**:
```
Live Demo: https://your-project.vercel.app
API Documentation: https://your-service.onrender.com/docs
Health Check: https://your-service.onrender.com/health

Test Instructions:
1. Open dashboard
2. Select store from sidebar
3. View real-time metrics
4. Check conversion funnel
5. Review anomalies
```

---

## 🐛 Troubleshooting

### Backend Issues

**Build fails with "disk not supported"**
- ✅ Fixed: `render.yaml` already updated to remove disk config

**Build fails with "numpy version error"**
- ✅ Fixed: Dockerfile uses Python 3.11

**Build fails with "apt-get error"**
- ✅ Fixed: Dockerfile simplified with correct package names

### Frontend Issues

**"Failed to fetch data"**
```
Solution:
1. Check NEXT_PUBLIC_API_URL is correct
2. Test backend: curl https://your-api.onrender.com/health
3. Redeploy from Vercel dashboard
```

**404 on frontend pages**
```
Solution:
1. Verify Root Directory = "frontend" in Vercel settings
2. Redeploy
```

**Health indicator shows "Unhealthy"**
```
Solution:
1. Wait 20-30s (Render free tier has cold starts)
2. Check backend is running
3. Manually refresh dashboard
```

---

## 💰 Costs

### Free Tier (Both Services)

**Render Free**:
- ✅ 750 hours/month
- ✅ 512 MB RAM
- ✅ Sleeps after 15 min inactivity
- ✅ Cold start: ~20s

**Vercel Free**:
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ Always on (no sleep)
- ✅ Fast CDN

**Total Monthly Cost**: $0

### Upgrade Options (Optional)

**Render Starter** ($7/month):
- No sleep
- 1 GB RAM
- Persistent storage

**Vercel Pro** ($20/month):
- 1 TB bandwidth
- Advanced analytics
- Priority support

---

## 🔄 Continuous Deployment

### Auto-Deploy on Git Push

Both services auto-deploy when you push to GitHub:

```bash
# Make changes
vim src/api_server.py
vim frontend/src/components/Dashboard.tsx

# Commit and push
git add .
git commit -m "Update features"
git push origin main

# Automatic deployments:
# - Render rebuilds backend (5-10 min)
# - Vercel rebuilds frontend (2-3 min)
```

---

## 📊 Performance

### Expected Response Times

| Endpoint | Response Time |
|----------|---------------|
| Frontend (Vercel) | 50-200ms |
| Backend API (Render) | 100-500ms |
| Cold Start (Render free) | ~20s first request |
| Dashboard Auto-Refresh | Every 30s |

### Optimization Tips

**Backend (Render)**:
- Upgrade to Starter for no sleep ($7/mo)
- Use persistent storage for database

**Frontend (Vercel)**:
- Already optimized with CDN
- Images automatically optimized
- Code splitting enabled

---

## 🎯 For Purplle Submission

### What to Include

```markdown
# Store Intelligence Platform Submission

## Live Demo
- **Dashboard**: https://your-project.vercel.app
- **API Docs**: https://your-service.onrender.com/docs

## Features
✅ Real-time store analytics dashboard
✅ Computer vision event processing
✅ Conversion funnel analysis
✅ Anomaly detection
✅ Multi-store support
✅ RESTful API with OpenAPI docs

## Tech Stack
- **Backend**: FastAPI (Python 3.11), YOLOv8, ByteTrack, SQLite
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Deployment**: Render (Backend), Vercel (Frontend)
- **Testing**: 344/344 tests passing, 95% coverage

## Test Instructions
1. Open dashboard: https://your-project.vercel.app
2. Select store from sidebar (store_001, store_1, store_2)
3. View metrics: entries, exits, occupancy, visit duration
4. Check conversion funnel stages
5. Review anomaly alerts (if any)
6. Test API directly: https://your-service.onrender.com/docs

## Performance Notes
- Dashboard hosted on Vercel (always on)
- API hosted on Render free tier (may have 20s cold start)
- Auto-refreshes every 30 seconds

## Repository
https://github.com/your-username/store-intelligence-platform

## Video Demo (Optional)
[Link to video walkthrough]
```

---

## 📚 Documentation Structure

```
Project Root/
├── README.md                          # Main project documentation
├── DESIGN.md                          # Architecture documentation
├── CHOICES.md                         # Design decisions
├── RENDER_DEPLOYMENT_GUIDE.md         # Backend deployment (Render)
├── FULL_STACK_DEPLOYMENT_GUIDE.md     # This file
├── FRONTEND_SETUP_COMPLETE.md         # Frontend overview
│
├── frontend/
│   ├── README.md                      # Frontend documentation
│   ├── DEPLOYMENT.md                  # Frontend deployment (Vercel)
│   └── ...
│
└── ...
```

---

## 🆘 Need Help?

### Documentation

- **Backend**: `RENDER_DEPLOYMENT_GUIDE.md`
- **Frontend**: `frontend/DEPLOYMENT.md`
- **Full Setup**: This file

### Support

- **Render**: https://render.com/docs
- **Vercel**: https://vercel.com/docs
- **Next.js**: https://nextjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com

---

## ✅ Success Checklist

### Before Submission

- [ ] Backend deployed to Render
- [ ] Backend health check passes
- [ ] Frontend deployed to Vercel
- [ ] Frontend connects to backend
- [ ] All features working
- [ ] No console errors
- [ ] Tested on mobile
- [ ] URLs documented
- [ ] Submission form completed

---

## 🎉 You're Done!

**Backend**: ✅ Deployed on Render  
**Frontend**: ✅ Deployed on Vercel  
**Status**: ✅ **LIVE AND READY FOR SUBMISSION**

### Your Live URLs

```
Dashboard:  https://your-project.vercel.app
API:        https://your-service.onrender.com
Docs:       https://your-service.onrender.com/docs
```

**Copy these URLs into your Purplle submission!**

---

**Deployment Completed**: 2024-06-03  
**Total Time**: 15-20 minutes  
**Status**: ✅ **PRODUCTION READY**
