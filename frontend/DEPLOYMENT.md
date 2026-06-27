# Frontend Deployment Guide - Vercel

Complete guide to deploy the Store Intelligence Platform frontend to Vercel.

## Prerequisites

✅ Backend API deployed to Render (get URL from Render dashboard)  
✅ GitHub repository with frontend code  
✅ Vercel account (free - sign up at vercel.com)

---

## 🚀 Quick Deploy (5 Minutes)

### Step 1: Push Frontend to GitHub

```bash
# From project root
git add frontend/
git commit -m "Add Next.js frontend dashboard"
git push origin main
```

### Step 2: Import to Vercel

1. Go to **[vercel.com](https://vercel.com)**
2. Click **"Add New"** → **"Project"**
3. Click **"Import"** next to your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: leave empty (default)
   - **Install Command**: `npm install` (default)

### Step 3: Add Environment Variable

1. Before deploying, click **"Environment Variables"**
2. Add:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://your-service.onrender.com` (your Render URL)
   - **Environment**: Select all (Production, Preview, Development)
3. Click **"Add"**

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes for build to complete
3. Get your URL: `https://your-project.vercel.app`

---

## ✅ Verify Deployment

### Test Your Frontend

1. **Open Dashboard**
   ```
   https://your-project.vercel.app
   ```

2. **Check Health Status**
   - Top-right corner should show "Healthy" with green indicator
   - If red/unhealthy, check API URL

3. **Test Metrics**
   - Select a store from sidebar
   - Should see metrics cards populate
   - Check conversion funnel chart
   - Verify anomalies section loads

### Troubleshooting

**Issue: "Failed to fetch data"**
```
Solution:
1. Check NEXT_PUBLIC_API_URL is correct
2. Verify backend API is running (test: https://your-api.onrender.com/health)
3. Redeploy: Vercel Dashboard → Deployments → Latest → "Redeploy"
```

**Issue: 404 on pages**
```
Solution:
1. Verify Root Directory is set to "frontend"
2. Rebuild: Settings → General → Root Directory → Save → Redeploy
```

---

## 🔧 Configuration Details

### Environment Variables

| Variable | Value | Required | Description |
|----------|-------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-api.onrender.com` | ✅ Yes | Backend API base URL |

**Important**: 
- Must start with `NEXT_PUBLIC_` to be accessible in browser
- No trailing slash
- Use HTTPS for production

### Build Settings

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "outputDirectory": ".next"
}
```

### Vercel Project Settings

**General Settings:**
- Framework: Next.js
- Root Directory: `frontend`
- Node.js Version: 20.x (default)

**Build & Development Settings:**
- Build Command: `npm run build`
- Output Directory: (empty - uses default)
- Install Command: `npm install`
- Development Command: `npm run dev`

---

## 📊 Expected Performance

### Vercel Free Tier

| Metric | Value |
|--------|-------|
| Build Time | 2-3 minutes |
| Cold Start | 1-2 seconds |
| Hot Response | 50-200ms |
| Bandwidth | 100 GB/month |
| Builds | Unlimited |
| Team Members | 1 (Free) |

### Optimization

Vercel automatically provides:
- ✅ Global CDN
- ✅ Edge caching
- ✅ Image optimization
- ✅ Automatic HTTPS
- ✅ Preview deployments (PRs)
- ✅ Analytics

---

## 🔄 Continuous Deployment

### Auto-Deploy on Git Push

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes
vim frontend/src/components/Dashboard.tsx

# Commit and push
git add frontend/
git commit -m "Update dashboard layout"
git push origin main

# Vercel automatically:
# 1. Detects push
# 2. Builds project
# 3. Deploys to production
# 4. Sends deployment notification
```

### Preview Deployments

For each pull request, Vercel creates a preview deployment:

1. Create feature branch
2. Make changes
3. Push and create PR
4. Vercel comments on PR with preview URL
5. Test preview before merging

---

## 🌐 Custom Domain (Optional)

### Add Custom Domain

1. Go to **Vercel Dashboard** → Your Project
2. Click **Settings** → **Domains**
3. Click **"Add"**
4. Enter your domain: `dashboard.yourdomain.com`
5. Follow DNS configuration instructions
6. Wait for DNS propagation (5-30 minutes)

### DNS Configuration

**For Apex Domain** (example.com):
```
Type: A
Name: @
Value: 76.76.21.21
```

**For Subdomain** (dashboard.example.com):
```
Type: CNAME
Name: dashboard
Value: cname.vercel-dns.com
```

---

## 📱 Mobile Responsiveness

The dashboard is fully responsive:

- **Desktop**: 1920x1080+ (4-column grid)
- **Tablet**: 768px-1919px (2-column grid)
- **Mobile**: <768px (1-column stack)

Test on mobile:
```
# Use Chrome DevTools Device Toolbar
# Or scan QR code from Vercel deployment
```

---

## 🔐 Security

### HTTPS

- Vercel automatically provides HTTPS
- All traffic encrypted
- Free SSL certificates
- Auto-renewal

### Environment Variables

- Stored securely in Vercel
- Not exposed in logs
- Separate per environment
- Can be encrypted

### CORS

Backend already configured to allow requests from any origin. For production, update backend CORS to only allow your Vercel domain:

```python
# In src/api_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-project.vercel.app"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📈 Monitoring

### Vercel Analytics

1. Go to **Analytics** tab in Vercel Dashboard
2. View:
   - Page views
   - Unique visitors
   - Performance metrics
   - Real User Monitoring (RUM)

### Custom Monitoring

Add Sentry, LogRocket, or other monitoring:

```bash
npm install @sentry/nextjs
# Follow Sentry setup guide
```

---

## 🎨 Customization After Deployment

### Update API URL

1. Go to **Settings** → **Environment Variables**
2. Edit `NEXT_PUBLIC_API_URL`
3. Click **"Save"**
4. Go to **Deployments** → **"Redeploy"**

### Change Branding

Update in repository:
```bash
# Edit logo/colors
vim frontend/src/components/Sidebar.tsx
vim frontend/tailwind.config.ts

# Push changes
git push origin main
# Auto-deploys in 2-3 minutes
```

---

## 💰 Pricing

### Free Tier (Hobby)
- ✅ Perfect for demos and personal projects
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ 1 team member
- ✅ Community support

### Pro Tier ($20/month)
- ✅ Commercial projects
- ✅ 1 TB bandwidth/month
- ✅ Unlimited team members
- ✅ Priority support
- ✅ Advanced analytics

---

## 🎯 For Purplle Submission

### Include in Submission

```
Frontend URL: https://your-project.vercel.app
Backend URL: https://your-service.onrender.com

Features Demonstrated:
✅ Real-time store metrics dashboard
✅ Conversion funnel visualization
✅ Anomaly detection alerts
✅ Health monitoring
✅ Multi-store support
✅ Responsive design

Tech Stack:
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.11
- Deployment: Vercel (Frontend), Render (Backend)

Test Instructions:
1. Open dashboard URL
2. Select store from sidebar (store_001, store_1, store_2)
3. View real-time metrics
4. Check conversion funnel
5. Review anomalies (if any)
6. Test health indicator (top-right)

Note: Dashboard hosted on Vercel free tier, auto-refreshes every 30s
```

---

## 🆘 Support

### Vercel Documentation
- [Next.js on Vercel](https://vercel.com/docs/frameworks/nextjs)
- [Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Custom Domains](https://vercel.com/docs/custom-domains)

### Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check `npm run build` locally first |
| API not connecting | Verify `NEXT_PUBLIC_API_URL` is correct |
| Slow loading | Check backend API response time |
| 404 errors | Verify Root Directory = `frontend` |

---

**Deployment Time**: 5-10 minutes  
**Status**: ✅ Ready to Deploy  
**Difficulty**: Easy

---

**Last Updated**: 2024-06-03  
**Vercel Version**: Latest  
**Next.js Version**: 14.1.0
