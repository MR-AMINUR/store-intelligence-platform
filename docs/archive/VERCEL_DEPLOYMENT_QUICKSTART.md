# Vercel Deployment - Quick Start Guide

**Deploy your frontend in 10 minutes** ⚡

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure:

- [ ] ✅ Backend is deployed on Render (get your backend URL ready)
- [ ] ✅ Frontend works locally (`npm run dev` in frontend directory)
- [ ] ✅ Code is pushed to GitHub
- [ ] ✅ You have a Vercel account (free - [vercel.com/signup](https://vercel.com/signup))

---

## 🚀 Deployment Steps

### Step 1: Get Your Backend URL

First, you need your Render backend URL. Open your Render dashboard:

```
https://dashboard.render.com
```

Find your service and copy the URL. It looks like:
```
https://store-intelligence-api-xxxx.onrender.com
```

**Important**: Copy this URL - you'll need it in Step 4!

---

### Step 2: Verify Local Build Works

Before deploying, test the build locally:

```bash
cd frontend
npm run build
```

Expected output:
```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (5/5)
✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /                                    5.02 kB        92.1 kB
└ ○ /_not-found                          871 B          87.9 kB
```

**If build fails**, fix errors before proceeding to Vercel.

**If build succeeds**, continue to Step 3.

---

### Step 3: Push to GitHub (If Not Already Done)

```bash
# From project root directory
cd d:/projects-intern/store-intelligence-platform

# Check status
git status

# Add frontend files
git add frontend/

# Commit
git commit -m "Add Next.js frontend dashboard for deployment"

# Push to GitHub
git push origin main
```

**Verify**: Check your GitHub repository - the `frontend/` folder should be visible.

---

### Step 4: Deploy to Vercel

#### 4.1 Login to Vercel

1. Go to **https://vercel.com**
2. Click **"Sign Up"** or **"Login"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your repositories

#### 4.2 Import Your Project

1. On Vercel dashboard, click **"Add New..."** button (top-right)
2. Select **"Project"** from dropdown
3. You'll see "Import Git Repository" page
4. Find your repository: `store-intelligence-platform`
5. Click **"Import"** button next to it

#### 4.3 Configure Project Settings

You'll see the "Configure Project" page. Fill in:

**Project Name**: (auto-filled, can customize)
```
store-intelligence-dashboard
```

**Framework Preset**: (auto-detected)
```
✓ Next.js
```

**Root Directory**: ⚠️ **IMPORTANT - Must change this!**
```
Click "Edit" → Type: frontend → Click "Continue"
```

**Build and Output Settings**: (keep defaults)
```
Build Command: npm run build
Output Directory: (leave empty)
Install Command: npm install
```

#### 4.4 Add Environment Variable

⚠️ **CRITICAL STEP** - Don't skip this!

1. Scroll down to **"Environment Variables"** section
2. Click to expand it
3. Add variable:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: Your Render backend URL (from Step 1)
     ```
     https://store-intelligence-api-xxxx.onrender.com
     ```
   - **Environments**: Select all three checkboxes:
     - [x] Production
     - [x] Preview  
     - [x] Development

4. Click **"Add"** button

**Double-check**: Make sure there's NO trailing slash in the URL!
- ✅ Correct: `https://your-api.onrender.com`
- ❌ Wrong: `https://your-api.onrender.com/`

#### 4.5 Deploy

1. Scroll to bottom
2. Click **"Deploy"** button
3. Wait 2-3 minutes (watch the build logs)

**Build Process**:
```
Building...
✓ Installing dependencies
✓ Building application
✓ Optimizing production build
✓ Deployment ready
```

---

### Step 5: Verify Deployment

#### 5.1 Get Your URL

After deployment completes, you'll see:
```
🎉 Congratulations! Your project has been deployed.

Visit: https://store-intelligence-dashboard-xxxx.vercel.app
```

Click the URL to open your dashboard.

#### 5.2 Test Dashboard Functionality

1. **Check Health Indicator** (top-right corner)
   - Should show green "Healthy" badge
   - If red/unhealthy, see Troubleshooting section

2. **Test Store Selection**
   - Click dropdown in sidebar
   - Select different stores (store_001, store_002, store_1, store_2)
   - Metrics should update when you change stores

3. **Verify All Components**
   - ✅ Metrics Cards (4 cards showing numbers)
   - ✅ Conversion Funnel Chart (bar chart)
   - ✅ Anomalies Table (may be empty - that's okay)
   - ✅ Last updated timestamp

4. **Test Auto-Refresh**
   - Wait 30 seconds
   - "Last updated" timestamp should change
   - Metrics refresh automatically

#### 5.3 Test in Browser Console

Open browser console (F12) and check:
```
✅ No red errors
✅ Should see: "API Client initialized with URL: https://..."
✅ Should see: "API Response: 200 /health"
✅ Should see: "API Response: 200 /stores/store_001/metrics"
```

---

## 🎯 Your Deployment URLs

After successful deployment, you'll have:

| Service | URL | Purpose |
|---------|-----|---------|
| **Backend** | `https://your-api.onrender.com` | FastAPI REST API |
| **Frontend** | `https://your-project.vercel.app` | Next.js Dashboard |
| **Health Check** | `https://your-api.onrender.com/health` | API status |
| **API Docs** | `https://your-api.onrender.com/docs` | Swagger UI |

**Save these URLs** for your project documentation!

---

## 🐛 Troubleshooting

### Issue 1: Build Failed on Vercel

**Symptom**: Red error message during build

**Solution**:
```bash
# Test build locally first
cd frontend
npm run build

# If it fails locally, fix errors
# Then push to GitHub
git push origin main

# Vercel will auto-deploy on push
```

**Common build errors**:
- TypeScript errors: Run `npm run type-check` to find issues
- Missing dependencies: Run `npm install` to ensure all packages installed
- Linting errors: Run `npm run lint` to find code issues

---

### Issue 2: Dashboard Shows "Failed to fetch data"

**Symptom**: Dashboard loads but shows error messages

**Root Causes**:
1. Backend API URL is wrong
2. Backend is not deployed/running
3. CORS issue

**Solution**:

**Check 1: Verify Backend URL**
```bash
# Test your backend health endpoint
curl https://your-api.onrender.com/health

# Should return:
{"status":"healthy","checks":{"database":"ok"},"response_time_ms":...}
```

**Check 2: Verify Environment Variable**
1. Go to Vercel Dashboard → Your Project
2. Click **Settings** → **Environment Variables**
3. Verify `NEXT_PUBLIC_API_URL` value is correct
4. If wrong, update it and click **"Save"**
5. Go to **Deployments** → Latest → **"Redeploy"**

**Check 3: Check Browser Console**
1. Open F12 (Developer Tools)
2. Go to **Console** tab
3. Look for errors:
   - ❌ `net::ERR_NAME_NOT_RESOLVED` → Backend URL is wrong
   - ❌ `CORS error` → Backend CORS not configured (should be already fixed)
   - ❌ `404 Not Found` → API endpoint wrong

---

### Issue 3: Health Indicator Shows "Unhealthy" (Red)

**Symptom**: Top-right shows red "Unhealthy" badge

**Solution**:

1. **Check Backend Health**:
   ```bash
   curl https://your-api.onrender.com/health
   ```

2. **If backend is sleeping** (Render free tier):
   - First request after 15 min of inactivity takes 30-60 seconds
   - Wait 60 seconds, then refresh dashboard
   - Health should turn green

3. **If still red**:
   - Check Render logs for backend errors
   - Verify backend database is accessible
   - Check Render service status

---

### Issue 4: 404 Error on Dashboard

**Symptom**: Opening dashboard shows "404 - Page Not Found"

**Root Cause**: Root Directory not set to `frontend`

**Solution**:
1. Go to Vercel Dashboard → Your Project
2. Click **Settings** → **General**
3. Scroll to **Root Directory**
4. Click **"Edit"**
5. Type: `frontend`
6. Click **"Save"**
7. Go to **Deployments** → **"Redeploy"**

---

### Issue 5: Styles Not Loading (Plain HTML)

**Symptom**: Dashboard shows content but no styling

**Root Cause**: CSS not building correctly

**Solution**:
```bash
# Rebuild locally to test
cd frontend
rm -rf .next
npm run build

# If successful, push to GitHub
git push origin main
```

---

### Issue 6: Can't Find Repository in Vercel

**Symptom**: Your repository doesn't show up in Vercel import list

**Solution**:
1. Click **"Adjust GitHub App Permissions"** link
2. Select **"All repositories"** or specific repository
3. Click **"Save"**
4. Go back to Vercel import page
5. Your repository should now appear

---

## 🔄 Updating Your Deployment

### Automatic Updates (Recommended)

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes to frontend
vim frontend/src/components/Dashboard.tsx

# Commit and push
git add frontend/
git commit -m "Update dashboard UI"
git push origin main

# Vercel automatically:
# 1. Detects the push
# 2. Runs npm run build
# 3. Deploys new version
# 4. Updates production URL
# 5. Sends you a notification
```

**Deployment time**: 2-3 minutes after push

### Manual Redeploy

If you need to redeploy without code changes (e.g., after changing environment variables):

1. Go to **Vercel Dashboard** → Your Project
2. Click **Deployments** tab
3. Find latest deployment
4. Click **"⋮"** (three dots) → **"Redeploy"**
5. Confirm **"Redeploy"**

---

## 🌐 Custom Domain (Optional)

Want to use your own domain instead of `.vercel.app`?

### Add Domain

1. Go to **Vercel Dashboard** → Your Project
2. Click **Settings** → **Domains**
3. Click **"Add"**
4. Enter your domain: `dashboard.yourdomain.com`
5. Follow DNS configuration instructions

### DNS Configuration

**For Subdomain** (dashboard.yourdomain.com):
```
Type: CNAME
Name: dashboard
Value: cname.vercel-dns.com
TTL: 300 (or automatic)
```

**For Apex Domain** (yourdomain.com):
```
Type: A
Name: @
Value: 76.76.21.21
TTL: 300 (or automatic)
```

**Wait**: DNS propagation takes 5-60 minutes

---

## 📊 Monitoring Your Deployment

### View Analytics

1. Go to **Vercel Dashboard** → Your Project
2. Click **Analytics** tab
3. View:
   - Real-time visitors
   - Page views
   - Performance metrics (Core Web Vitals)
   - Top pages
   - Traffic sources

### View Build Logs

1. Go to **Deployments** tab
2. Click on any deployment
3. Click **"Building"** or **"View Build Logs"**
4. See full npm install and build output

### View Runtime Logs

Vercel Edge Functions automatically log:
- API requests (timing, status)
- Console.log output
- Errors and warnings

**Note**: Frontend is static (no server-side logs), but API client logs appear in browser console.

---

## 💡 Best Practices

### Environment Variables

✅ **DO**:
- Use `NEXT_PUBLIC_` prefix for client-side variables
- Set all three environments (Production, Preview, Development)
- Use HTTPS URLs for production APIs
- No trailing slashes in URLs

❌ **DON'T**:
- Put secrets in `NEXT_PUBLIC_` variables (they're exposed to browser)
- Use HTTP in production (always HTTPS)
- Hardcode URLs in code

### Performance

Vercel automatically optimizes:
- ✅ Image optimization (WebP, lazy loading)
- ✅ Code splitting (smaller bundles)
- ✅ CDN caching (global edge network)
- ✅ Compression (Brotli/gzip)
- ✅ HTTP/2 (multiplexing)

Your dashboard should load in:
- **First visit**: 1-2 seconds
- **Return visit**: 200-500ms (cached)

### Security

- ✅ Automatic HTTPS (free SSL certificate)
- ✅ DDoS protection
- ✅ Environment variables encrypted
- ✅ No source code exposure

**Recommended**: Update backend CORS to only allow your Vercel domain:
```python
# In src/api_server.py (after deployment)
allow_origins=["https://your-project.vercel.app"]
```

---

## 📱 Mobile Testing

Test your dashboard on mobile devices:

### Using QR Code
1. Go to deployment URL
2. Vercel shows QR code on deployment success page
3. Scan with phone camera
4. Opens dashboard in mobile browser

### Using Chrome DevTools
1. Open dashboard in Chrome
2. Press F12
3. Click device toolbar icon (Ctrl+Shift+M)
4. Select device: iPhone 14, iPad, Pixel, etc.
5. Test responsive layout

Dashboard is fully responsive:
- **Mobile**: 1-column stack layout
- **Tablet**: 2-column grid
- **Desktop**: 4-column grid

---

## 🎓 Useful Vercel Commands (CLI)

Install Vercel CLI (optional):
```bash
npm install -g vercel
```

Useful commands:
```bash
# Login to Vercel
vercel login

# Deploy from command line
cd frontend
vercel

# Deploy to production
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls

# Remove project
vercel remove project-name
```

---

## 📝 Deployment Checklist

Use this checklist to verify deployment:

### Pre-Deployment
- [ ] Backend deployed on Render (get URL)
- [ ] Frontend builds locally (`npm run build`)
- [ ] Code pushed to GitHub
- [ ] Vercel account created

### During Deployment
- [ ] Project imported to Vercel
- [ ] Root directory set to `frontend`
- [ ] Environment variable `NEXT_PUBLIC_API_URL` added
- [ ] Deploy button clicked

### Post-Deployment
- [ ] Dashboard URL opens successfully
- [ ] Health indicator shows "Healthy" (green)
- [ ] Store dropdown works (4 stores available)
- [ ] Metrics cards display numbers
- [ ] Conversion funnel chart renders
- [ ] No console errors (F12)
- [ ] Auto-refresh works (wait 30 seconds)
- [ ] Test on mobile device

### Documentation
- [ ] Save deployment URL
- [ ] Save backend URL
- [ ] Document environment variables
- [ ] Note any issues encountered

---

## 🏆 Success Criteria

Your deployment is successful when:

✅ Dashboard loads at `https://your-project.vercel.app`  
✅ Health indicator shows "Healthy"  
✅ All 4 stores appear in dropdown  
✅ Metrics update when changing stores  
✅ Charts render correctly  
✅ No errors in browser console  
✅ Auto-refresh works every 30 seconds  
✅ Mobile responsive (test with F12 device toolbar)  

---

## 🆘 Get Help

### Vercel Support
- Documentation: https://vercel.com/docs
- Community: https://github.com/vercel/next.js/discussions
- Status: https://vercel-status.com

### Project Issues
- Check `DEPLOYMENT.md` for detailed troubleshooting
- Review backend logs in Render dashboard
- Test API endpoints with curl/Postman

---

## 📋 Summary

**What You Did:**
1. ✅ Verified local build works
2. ✅ Pushed code to GitHub
3. ✅ Imported project to Vercel
4. ✅ Configured root directory (`frontend`)
5. ✅ Added environment variable (`NEXT_PUBLIC_API_URL`)
6. ✅ Deployed to production

**What You Got:**
- 🌐 Live dashboard URL
- ⚡ Automatic deployments on git push
- 🔒 HTTPS with free SSL
- 📊 Built-in analytics
- 🌍 Global CDN (fast worldwide)

**Deployment Time:** 5-10 minutes  
**Build Time:** 2-3 minutes per deploy  
**Cost:** FREE (Vercel Hobby tier)

---

**🎉 Congratulations!** Your Store Intelligence Dashboard is now live on Vercel!

**Next Steps:**
- Share your dashboard URL
- Monitor analytics
- Update deployment when you push new features
- (Optional) Add custom domain

---

**Quick Reference:**

```bash
# Test locally
cd frontend && npm run build

# Push to GitHub
git add frontend/ && git commit -m "Deploy" && git push

# Vercel auto-deploys from GitHub
# View at: https://your-project.vercel.app
```

**Your URLs:**
- Frontend: `https://your-project.vercel.app`
- Backend: `https://your-api.onrender.com`
- API Docs: `https://your-api.onrender.com/docs`

**Environment Variable:**
```
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

**Build succeeds when you see:**
```
✓ Compiled successfully
✓ Generating static pages
✓ Finalizing page optimization
```

---

**Document Version:** 1.0  
**Last Updated:** 2024-06-27  
**Deployment Platform:** Vercel  
**Framework:** Next.js 14.1.0
