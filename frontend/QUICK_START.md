# Frontend Quick Start ⚡

**Time**: 5 minutes to run locally | 5 minutes to deploy

---

## 🚀 Run Locally (5 minutes)

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies (2-3 minutes)
npm install

# 3. Start development server
npm run dev

# 4. Open browser
# http://localhost:3000
```

**Expected Result**: Dashboard loads with metrics from your backend API.

---

## 🌐 Deploy to Vercel (5 minutes)

### Method 1: Vercel Dashboard (Recommended)

```bash
# 1. Push to GitHub
git add frontend/
git commit -m "Add frontend"
git push origin main

# 2. Go to vercel.com
# 3. Click "Add New" → "Project"
# 4. Select repository
# 5. Set Root Directory: frontend
# 6. Add Environment Variable:
#    Key: NEXT_PUBLIC_API_URL
#    Value: https://your-service.onrender.com
# 7. Click "Deploy"

# ✅ Done! Get URL in 2-3 minutes
```

### Method 2: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Follow prompts, then:
vercel --prod
```

---

## ✅ Verify

### Local
```bash
# Health indicator (top-right) shows "Healthy"
# Metrics cards show numbers
# Conversion funnel displays
# No console errors
```

### Production
```bash
# Open your Vercel URL
# Check health indicator
# Test store selection
# Verify metrics update
```

---

## 🔧 Configuration

### Environment Variable

**Local** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production** (Vercel):
```bash
NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

---

## 📚 Full Documentation

- **Setup**: `frontend/README.md`
- **Deployment**: `frontend/DEPLOYMENT.md`
- **Overview**: `FRONTEND_SETUP_COMPLETE.md`

---

## 🆘 Troubleshooting

**"Failed to fetch data"**
→ Check `NEXT_PUBLIC_API_URL` is correct

**Build fails**
→ Run `npm run build` locally to test

**Health shows "Unhealthy"**
→ Wait 20s (Render cold start), then refresh

---

**Status**: ✅ Ready  
**Time**: 5 minutes
