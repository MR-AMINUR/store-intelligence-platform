# Frontend-Backend Connection - Complete Fix

## ✅ Issues Fixed

1. **API Client** - Rewrote with proper error handling and logging
2. **Environment Variable** - Fixed `.env.local` to point to `http://localhost:8000`
3. **Query Parameters** - Using axios params instead of manual URL construction
4. **CORS** - Already configured correctly in backend
5. **Logging** - Added console logging for debugging

## 🚀 How to Start Everything

### Step 1: Start Backend (Terminal 1)

```bash
# From project root
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Verify Backend Works

```bash
# In another terminal
curl http://localhost:8000/health
```

**Expected:**
```json
{"status":"healthy","checks":{"database":"ok"},"response_time_ms":2.05,"timestamp":"..."}
```

### Step 3: Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000
- Ready in 2.3s
```

### Step 4: Open Browser

1. Go to: **http://localhost:3000**
2. Open DevTools (F12) → Console tab
3. You should see:
   ```
   API Client initialized with URL: http://localhost:8000
   API Request: GET http://localhost:8000/health
   API Response: 200 /health
   API Request: GET http://localhost:8000/stores/store_001/metrics
   API Response: 200 /stores/store_001/metrics
   ...
   ```

## 🔍 Debugging Checklist

### If Health Indicator Shows "Checking..." Forever

**Cause**: Frontend can't connect to backend

**Check**:
1. Is backend running? Look for "Uvicorn running on..." message
2. Test backend directly: `curl http://localhost:8000/health`
3. Check browser console for CORS errors
4. Verify `.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Fix**:
```bash
# Restart backend
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload

# Restart frontend  
cd frontend
# Ctrl+C to stop, then:
npm run dev
```

### If You See "Network Error"

**Cause**: API URL is wrong or backend is not accessible

**Check Browser Console**:
```
Failed to load resource: net::ERR_CONNECTION_REFUSED
```

**Fix**:
1. Verify backend is running on port 8000
2. Check `.env.local` in frontend directory
3. Restart frontend dev server

### If You See "Store not found"

**Cause**: Database is empty

**Fix**:
```bash
python add_test_data.py
```

This adds 584 test events to the database.

### If Metrics Show But Funnel Doesn't

**Cause**: API endpoint might be failing

**Check Backend Logs**: Look for 404 or 500 errors

**Test Endpoint**:
```bash
curl http://localhost:8000/stores/store_001/funnel
```

## 📊 Test All Endpoints

```bash
# Health
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/stores/store_001/metrics

# Funnel
curl http://localhost:8000/stores/store_001/funnel

# Anomalies
curl http://localhost:8000/stores/store_001/anomalies?time_window=24

# Heatmap
curl http://localhost:8000/stores/store_001/heatmap?resolution=50
```

All should return JSON data.

## ✅ Success Criteria

Your setup is working when:

1. ✅ Backend terminal shows: "Uvicorn running on http://0.0.0.0:8000"
2. ✅ `curl http://localhost:8000/health` returns `{"status":"healthy"}`
3. ✅ Frontend shows "Healthy" badge (top-right, green)
4. ✅ Metrics cards show numbers (50, 45, 5, 2m)
5. ✅ Conversion funnel displays with stages
6. ✅ No red error boxes on dashboard
7. ✅ Browser console shows "API Response: 200" messages

## 🆘 Still Having Issues?

### Quick Reset

```bash
# Terminal 1: Stop and restart backend
# Ctrl+C
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Stop and restart frontend
# Ctrl+C
cd frontend
npm run dev

# Browser: Hard refresh
# Windows/Linux: Ctrl+Shift+R
# Mac: Cmd+Shift+R
```

### Check Ports

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# If port 8000 is in use by something else, kill it or use different port
```

### Clear Everything

```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev

# Clear browser cache
# In DevTools → Network tab → Check "Disable cache"
```

## 📝 Environment Variables Reference

### Frontend (`.env.local`)

```bash
# Local Development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (Render)
# NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

**Important**: 
- Must start with `NEXT_PUBLIC_` to be accessible in browser
- No trailing slash
- Must restart dev server after changing

### Backend (`.env` or environment)

```bash
DB_PATH=data/events.db
LOG_LEVEL=INFO
YOLO_MODEL_PATH=models/yolov8n.pt
CONFIDENCE_THRESHOLD=0.5
TRACKER_MAX_AGE=30
ZONE_CONFIG_PATH=config/zones.json
STORE_ID=store_001
```

## 🎯 Expected Dashboard

Once working, you should see:

### Top Section
- **Title**: "Store Analytics"
- **Subtitle**: "Real-time insights for store_001"
- **Health Badge**: "Healthy" (green) with response time
- **Refresh Button**: Working, not spinning continuously
- **Last Updated**: Shows current time

### Metrics Cards (4 cards)
1. **Total Entries**: 50 (green icon)
2. **Total Exits**: 45 (red icon)
3. **Current Occupancy**: 5 (blue icon)
4. **Avg Visit Duration**: 2m 0s (purple icon)

### Conversion Funnel
- Stage 1: Store Entries - 50 customers - 100%
- Stage 2: Zone Visits - 40 customers - 80%
- Stage 3: Queue Joins - 0 customers - 0%
- Stage 4: Purchases - 0 customers - 0%
- Overall Conversion Rate: 0.0%

### Anomalies
- Shows "No anomalies detected" with green checkmark
- Or lists any detected anomalies

---

**Last Updated**: 2024-06-03  
**Status**: ✅ All issues fixed
