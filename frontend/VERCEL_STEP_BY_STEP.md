# Vercel Deployment - Visual Step-by-Step Guide

Complete visual walkthrough with screenshots descriptions for deploying to Vercel.

---

## 🎯 What You'll Deploy

**Frontend Dashboard Features:**
- ✅ Real-time store metrics
- ✅ Conversion funnel visualization
- ✅ Anomaly detection alerts
- ✅ Multi-store support
- ✅ Health monitoring
- ✅ Auto-refresh every 30 seconds

**Tech Stack:**
- Next.js 14 + TypeScript
- Tailwind CSS
- Recharts for visualizations
- Axios for API calls

---

## ⏱️ Time Required

- **First-time deployment**: 10-15 minutes
- **Subsequent deployments**: Automatic (2-3 minutes)

---

## 📸 Step-by-Step Screenshots Guide

### Step 1: Prepare Backend URL

**What you'll do:** Get your Render backend URL

**Where:** Render Dashboard (https://dashboard.render.com)

**Visual Steps:**

```
┌─────────────────────────────────────────────────────────┐
│  Render Dashboard                                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Services                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  store-intelligence-api        [Active]         │   │
│  │  https://store-api-xxxx.onrender.com            │ ← Copy this!
│  │                                                  │   │
│  │  Last Deploy: 2 hours ago                       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Action:**
1. Login to Render
2. Find your service
3. Copy the URL (looks like: `https://store-intelligence-api-xxxx.onrender.com`)
4. **Save it** - you'll need it in Step 4!

---

### Step 2: Test Local Build

**What you'll do:** Verify the frontend builds without errors

**Where:** Your terminal

**Visual Steps:**

```
Terminal:
┌─────────────────────────────────────────────────────────┐
│ $ cd frontend                                           │
│ $ npm run build                                         │
│                                                         │
│ > store-intelligence-dashboard@1.0.0 build             │
│ > next build                                            │
│                                                         │
│   ▲ Next.js 14.1.0                                     │
│                                                         │
│   ✓ Creating an optimized production build             │
│   ✓ Compiled successfully                              │
│   ✓ Linting and checking validity of types             │
│   ✓ Collecting page data                               │
│   ✓ Generating static pages (5/5)                      │
│   ✓ Finalizing page optimization                       │
│                                                         │
│ Route (app)                Size     First Load JS      │
│ ┌ ○ /                      5.02 kB        92.1 kB      │
│ └ ○ /_not-found            871 B          87.9 kB      │
│                                                         │
│ Build completed in 23.5s                               │
└─────────────────────────────────────────────────────────┘
```

✅ **Success indicators:**
- "Compiled successfully" message
- No red error messages
- Build time shown

❌ **If you see errors:**
- Fix TypeScript/lint errors first
- Run `npm run lint` to find issues
- Run `npm run type-check` for type errors

---

### Step 3: Push to GitHub

**What you'll do:** Push your frontend code to GitHub

**Where:** Your terminal

**Visual Steps:**

```
Terminal:
┌─────────────────────────────────────────────────────────┐
│ $ git status                                            │
│ On branch main                                          │
│ Untracked files:                                        │
│   frontend/                                             │
│                                                         │
│ $ git add frontend/                                     │
│ $ git commit -m "Add Next.js dashboard for deployment" │
│ [main abc1234] Add Next.js dashboard                   │
│  24 files changed, 1847 insertions(+)                  │
│                                                         │
│ $ git push origin main                                  │
│ Enumerating objects: 30, done.                         │
│ Counting objects: 100% (30/30), done.                  │
│ Writing objects: 100% (30/30), 125.34 KiB | 4.54 MiB/s │
│ To https://github.com/username/store-intelligence.git  │
│    abc1234..def5678  main -> main                      │
└─────────────────────────────────────────────────────────┘
```

**Verify on GitHub:**

```
GitHub Repository View:
┌─────────────────────────────────────────────────────────┐
│  username / store-intelligence-platform                 │
├─────────────────────────────────────────────────────────┤
│  📁 backend/                                            │
│  📁 data/                                               │
│  📁 frontend/          ← Should see this folder!        │
│  📁 models/                                             │
│  📁 src/                                                │
│  📄 README.md                                           │
│  📄 requirements.txt                                    │
└─────────────────────────────────────────────────────────┘
```

---

### Step 4: Login to Vercel

**What you'll do:** Create/login to Vercel account

**Where:** https://vercel.com

**Visual Steps:**

```
Vercel Homepage:
┌─────────────────────────────────────────────────────────┐
│                                                         │
│          ▲ Vercel                                      │
│                                                         │
│     Develop. Preview. Ship.                            │
│                                                         │
│     [Sign Up]  [Login]                                 │ ← Click here!
│                                                         │
└─────────────────────────────────────────────────────────┘

Login Page:
┌─────────────────────────────────────────────────────────┐
│  Continue with:                                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  🐙 Continue with GitHub                        │   │ ← Click this!
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  🦊 Continue with GitLab                        │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  📊 Continue with Bitbucket                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

GitHub Authorization:
┌─────────────────────────────────────────────────────────┐
│  Authorize Vercel                                       │
│                                                         │
│  Vercel by Vercel would like permission to:            │
│  • Read access to code                                 │
│  • Read and write access to commit statuses            │
│                                                         │
│  [Cancel]  [Authorize vercel]                          │ ← Click!
└─────────────────────────────────────────────────────────┘
```

---

### Step 5: Import Project to Vercel

**What you'll do:** Import your GitHub repository

**Where:** Vercel Dashboard

**Visual Steps:**

```
Vercel Dashboard:
┌─────────────────────────────────────────────────────────┐
│  Overview  Projects  Storage  Settings                  │
│                                                         │
│  Welcome to Vercel!              [Add New... ▼]        │ ← Click!
│                                                         │
│  Start by importing a project                          │
└─────────────────────────────────────────────────────────┘

Dropdown Menu:
┌───────────────────────────┐
│  Project                  │ ← Select this!
│  Team                     │
│  Domain                   │
└───────────────────────────┘

Import Git Repository:
┌─────────────────────────────────────────────────────────┐
│  Import Git Repository                                  │
│                                                         │
│  Search repositories...                                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  username/store-intelligence-platform           │   │
│  │  Updated 5 minutes ago                [Import]  │   │ ← Click Import!
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  username/other-project                         │   │
│  │  Updated 2 days ago                    [Import] │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Can't find your repository?**

```
┌─────────────────────────────────────────────────────────┐
│  Don't see your repository?                             │
│  [Adjust GitHub App Permissions →]                      │ ← Click here!
└─────────────────────────────────────────────────────────┘

GitHub Permissions:
┌─────────────────────────────────────────────────────────┐
│  Repository access                                      │
│                                                         │
│  ● All repositories                                     │ ← Select this
│  ○ Only select repositories                             │
│                                                         │
│  [Cancel]  [Save]                                       │
└─────────────────────────────────────────────────────────┘
```

---

### Step 6: Configure Project Settings

**What you'll do:** Set up build configuration

**Where:** Vercel Configure Project page

**Visual Steps:**

```
Configure Project:
┌─────────────────────────────────────────────────────────┐
│  Configure Project                                      │
│                                                         │
│  Project Name                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ store-intelligence-dashboard                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Framework Preset                                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Next.js  ✓                                      │   │ Auto-detected
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Root Directory                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ./                                      [Edit]  │   │ ← CLICK EDIT!
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**⚠️ CRITICAL: Edit Root Directory**

```
Edit Root Directory:
┌─────────────────────────────────────────────────────────┐
│  Root Directory                                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ frontend                                        │   │ ← Type "frontend"
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  The directory where your project code lives.          │
│                                                         │
│  [Cancel]  [Continue]                                  │ ← Click Continue
└─────────────────────────────────────────────────────────┘
```

**After setting Root Directory:**

```
Configure Project (continued):
┌─────────────────────────────────────────────────────────┐
│  Root Directory                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │ frontend ✓                              [Edit]  │   │ ← Verified!
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Build and Output Settings                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Build Command:     npm run build         ✓     │   │ Keep defaults
│  │ Output Directory:  (default)             ✓     │   │
│  │ Install Command:   npm install           ✓     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ▼ Environment Variables                         [▼]   │ ← Expand this!
└─────────────────────────────────────────────────────────┘
```

---

### Step 7: Add Environment Variable

**What you'll do:** Add your backend API URL

**Where:** Same page, Environment Variables section

**Visual Steps:**

```
Environment Variables (expanded):
┌─────────────────────────────────────────────────────────┐
│  ▼ Environment Variables                                │
│                                                         │
│  Add the environment variables used in your            │
│  project. Learn More →                                 │
│                                                         │
│  Key                                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ NEXT_PUBLIC_API_URL                             │   │ ← Type this
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Value (Will be encrypted)                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ https://store-api-xxxx.onrender.com            │   │ ← Paste your URL
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Environments                                          │
│  ☑ Production   ☑ Preview   ☑ Development            │ ← Check all!
│                                                         │
│  [Add]                                                 │ ← Click Add
└─────────────────────────────────────────────────────────┘
```

**After adding:**

```
Environment Variables (with variable added):
┌─────────────────────────────────────────────────────────┐
│  ▼ Environment Variables                                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ NEXT_PUBLIC_API_URL                             │   │
│  │ https://store-api-xxxx.onrender.com            │   │
│  │ Production, Preview, Development        [Edit]  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [Add Another]                                         │
└─────────────────────────────────────────────────────────┘
```

✅ **Verify:**
- Key is `NEXT_PUBLIC_API_URL` (exact spelling!)
- Value is your Render URL (NO trailing slash!)
- All three environments checked

---

### Step 8: Deploy

**What you'll do:** Start the deployment

**Where:** Bottom of Configure Project page

**Visual Steps:**

```
Bottom of page:
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Review your settings above, then:                     │
│                                                         │
│  [Deploy]                                              │ ← Click Deploy!
└─────────────────────────────────────────────────────────┘

Building... (Wait 2-3 minutes):
┌─────────────────────────────────────────────────────────┐
│  🔨 Building                                            │
│                                                         │
│  Cloning repository...                          ✓      │
│  Installing dependencies...                     ✓      │
│  Building application...                        ⏳     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ > next build                                    │   │
│  │   ▲ Next.js 14.1.0                             │   │
│  │   ✓ Creating an optimized production build     │   │
│  │   ✓ Compiled successfully                      │   │
│  │   ✓ Collecting page data                       │   │
│  │   ✓ Generating static pages (5/5)              │   │
│  │   ✓ Finalizing page optimization               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Uploading build outputs...                     ⏳     │
│  Deploying...                                   ⏳     │
└─────────────────────────────────────────────────────────┘
```

---

### Step 9: Deployment Success

**What you'll see:** Success page with your URL

**Where:** Vercel deployment result page

**Visual Steps:**

```
🎉 Deployment Success!
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🎊 Congratulations!                                   │
│                                                         │
│  Your project has been successfully deployed.          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                  │   │
│  │  store-intelligence-dashboard.vercel.app        │   │
│  │  ↗                                               │   │
│  │                                                  │   │
│  │  [Visit]                                        │   │ ← Click to open!
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Deployment Details:                                   │
│  • Status: Ready                                       │
│  • Deployed: Just now                                  │
│  • Build Time: 2m 34s                                  │
│  • Production: ✓                                       │
│                                                         │
│  [View Project Dashboard]                              │
└─────────────────────────────────────────────────────────┘
```

**Copy your URL!** You'll need it for documentation.

---

### Step 10: Verify Dashboard

**What you'll do:** Test your live dashboard

**Where:** Your Vercel URL (e.g., https://your-project.vercel.app)

**Visual Steps:**

```
Your Live Dashboard:
┌─────────────────────────────────────────────────────────┐
│  Store Intel                    [Healthy ✓]  [Refresh] │
│  Analytics Platform                                     │
├─────────────────────────────────────────────────────────┤
│  SELECT STORE                  Store Analytics         │
│  ┌──────────────────────┐                              │
│  │ Store 001 - Downtown │      Real-time insights for  │
│  └──────────────────────┘      store_001               │
│                                                         │
│  ✓ Overview                    Last updated: 10:30:45  │
│    Metrics                                              │
│    Heatmap            ┌──────────┐ ┌──────────┐       │
│    Anomalies          │  Total   │ │  Total   │       │
│                       │  Entries │ │  Exits   │       │
│                       │   100    │ │    90    │       │
│  Settings             └──────────┘ └──────────┘       │
│                                                         │
│  © 2024               ┌──────────┐ ┌──────────┐       │
│  v1.0.0               │ Current  │ │   Avg    │       │
│                       │Occupancy │ │  Visit   │       │
│                       │    10    │ │  9.3 min │       │
│                       └──────────┘ └──────────┘       │
│                                                         │
│                       Conversion Funnel                │
│                       [Chart visualization...]         │
└─────────────────────────────────────────────────────────┘
```

**Check these items:**

✅ **Visual Checks:**
- [ ] Health indicator shows "Healthy" (green)
- [ ] Store dropdown works (4 stores available)
- [ ] Metrics cards show numbers (not "Loading...")
- [ ] Conversion funnel chart renders
- [ ] No error messages visible

✅ **Functional Checks:**
- [ ] Select different stores - metrics update
- [ ] Wait 30 seconds - auto-refresh works
- [ ] Refresh button works (top-right)
- [ ] Responsive on mobile (F12 → device toolbar)

✅ **Browser Console (F12):**

```
Console:
┌─────────────────────────────────────────────────────────┐
│  ✓ API Client initialized with URL: https://...        │
│  ✓ API Request: GET https://.../health                 │
│  ✓ API Response: 200 /health                           │
│  ✓ API Request: GET https://.../stores/store_001/...   │
│  ✓ API Response: 200 /stores/store_001/metrics         │
│  ✓ API Response: 200 /stores/store_001/funnel          │
└─────────────────────────────────────────────────────────┘
```

❌ **If you see errors in console:**
- Red "Failed to fetch" → Check environment variable
- 404 errors → Check root directory setting
- CORS errors → Check backend CORS config

---

## ✅ Success Checklist

Your deployment is complete when ALL items are checked:

**Deployment:**
- [ ] Project imported to Vercel
- [ ] Root directory set to `frontend`
- [ ] Environment variable added (`NEXT_PUBLIC_API_URL`)
- [ ] Build completed successfully
- [ ] Deployment URL received

**Functionality:**
- [ ] Dashboard loads (no 404)
- [ ] Health indicator is green
- [ ] All 4 stores in dropdown
- [ ] Metrics display correctly
- [ ] Charts render properly
- [ ] No console errors (F12)
- [ ] Auto-refresh works (30s)
- [ ] Mobile responsive (F12 device toolbar)

**Documentation:**
- [ ] Saved frontend URL
- [ ] Saved backend URL
- [ ] Tested all features
- [ ] Ready to submit/share

---

## 🎊 Congratulations!

Your Store Intelligence Dashboard is now live on Vercel!

**What you've achieved:**
- ✅ Professional production deployment
- ✅ Global CDN delivery (fast worldwide)
- ✅ Automatic HTTPS with SSL
- ✅ Auto-deploys on git push
- ✅ Built-in analytics
- ✅ Free hosting

**Next Steps:**
1. Share your dashboard URL
2. Monitor Vercel analytics
3. (Optional) Add custom domain
4. Push updates to auto-deploy

**Your URLs:**
```
Frontend: https://your-project.vercel.app
Backend:  https://your-api.onrender.com
API Docs: https://your-api.onrender.com/docs
```

---

## 📚 Additional Resources

- **Quick Reference:** `VERCEL_DEPLOY.txt`
- **Detailed Guide:** `VERCEL_DEPLOYMENT_QUICKSTART.md`
- **Troubleshooting:** `DEPLOYMENT.md`
- **Vercel Docs:** https://vercel.com/docs

---

**Deployment Time:** 10 minutes  
**Build Time:** 2-3 minutes  
**Cost:** FREE (Vercel Hobby tier)  
**Difficulty:** Easy ✨

