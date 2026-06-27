# Vercel Deployment - Quick Reference Card

**Print this or keep open while deploying!**

---

## ⚡ 5-Minute Checklist

```
□ Step 1: Get backend URL from Render
□ Step 2: Test: cd frontend && npm run build
□ Step 3: Push: git push origin main
□ Step 4: Vercel → Add New → Project → Import repo
□ Step 5: Root Directory = "frontend" ⚠️ MUST CHANGE!
□ Step 6: Add env var: NEXT_PUBLIC_API_URL = [backend URL]
□ Step 7: Click Deploy → Wait 2-3 min
□ Step 8: Verify dashboard works
```

---

## 🎯 Critical Settings

**Must Get Right:**

| Setting | Value | Where |
|---------|-------|-------|
| Root Directory | `frontend` | Configure Project page |
| Env Var Key | `NEXT_PUBLIC_API_URL` | Environment Variables section |
| Env Var Value | `https://your-api.onrender.com` | NO trailing slash! |
| Environments | All 3 checked | Production, Preview, Development |

---

## 🔴 Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Root Directory: `./` | Root Directory: `frontend` |
| URL: `https://api.com/` | URL: `https://api.com` (no slash!) |
| Key: `API_URL` | Key: `NEXT_PUBLIC_API_URL` |
| Only Production checked | All 3 environments checked |

---

## 📍 Important URLs

**Vercel:**
- Login: https://vercel.com
- Dashboard: https://vercel.com/dashboard
- Docs: https://vercel.com/docs

**Your Render Backend:**
```
Write here: https://________________________________.onrender.com
```

**Your Vercel Frontend (after deploy):**
```
Write here: https://________________________________.vercel.app
```

---

## 🧪 Quick Tests

**After deployment, verify:**

```bash
# Test 1: Dashboard loads
✓ Open: https://your-project.vercel.app
✓ Should see: Dashboard with sidebar

# Test 2: Health indicator
✓ Look: Top-right corner
✓ Should be: Green "Healthy"

# Test 3: Store selection
✓ Click: Dropdown in sidebar
✓ Should see: 4 stores (store_001, store_002, store_1, store_2)

# Test 4: Metrics display
✓ Select: Any store
✓ Should show: Numbers in 4 cards

# Test 5: No console errors
✓ Press: F12
✓ Console tab: No red errors
✓ Should see: "API Client initialized with URL: https://..."
```

---

## 🔧 If Something Goes Wrong

**Build fails:**
```bash
cd frontend
npm run build
# Fix any errors shown
git push origin main
```

**Dashboard shows errors:**
```
1. Vercel → Your Project → Settings → Environment Variables
2. Check NEXT_PUBLIC_API_URL is correct
3. Deployments → Latest → Redeploy
```

**404 Not Found:**
```
1. Vercel → Settings → General → Root Directory
2. Change to: frontend
3. Save → Deployments → Redeploy
```

**Health shows "Unhealthy":**
```
1. Wait 60 seconds (backend cold start)
2. Refresh page
3. If still red, check Render backend status
```

---

## 📞 Quick Help

**Stuck?** Check these files:
1. `VERCEL_DEPLOY.txt` - Simple checklist
2. `VERCEL_STEP_BY_STEP.md` - Visual guide
3. `VERCEL_DEPLOYMENT_QUICKSTART.md` - Detailed walkthrough

**Vercel Docs:** https://vercel.com/docs/frameworks/nextjs

---

## ⏱️ Expected Times

- Import project: 30 seconds
- Configure settings: 2 minutes
- Build + Deploy: 2-3 minutes
- Total: ~5-6 minutes

---

## ✅ Success Indicators

**You're done when:**

✓ Vercel shows "🎉 Congratulations!"  
✓ Dashboard opens at vercel.app URL  
✓ Health is green  
✓ Stores dropdown works  
✓ Metrics show numbers  
✓ No console errors  

---

## 💾 Save These

After successful deployment:

```
Frontend URL: https://______________________________.vercel.app

Backend URL:  https://______________________________.onrender.com

Date Deployed: _______________

Build Time: ________ minutes
```

---

## 🎓 Pro Tips

1. **Bookmark Vercel dashboard** for quick access
2. **Test locally first**: `npm run build` before deploying
3. **Watch build logs** to catch errors early
4. **Use preview deployments** for testing (automatic on PRs)
5. **Auto-deploy enabled** by default on git push

---

**Quick Deploy Command Reference:**

```bash
# Full deployment in one go:
cd frontend && \
npm run build && \
cd .. && \
git add . && \
git commit -m "Deploy to Vercel" && \
git push origin main

# Then: Vercel auto-deploys in 2-3 minutes
```

---

**Print-Friendly Version**  
**Version:** 1.0  
**Platform:** Vercel  
**Framework:** Next.js 14
