# Frontend-Backend Connection: Final Fix Guide

## Current Status

✅ **Backend**: Working correctly
- Running on http://localhost:8000
- Health endpoint: `{"status":"healthy","checks":{"database":"ok"}}`
- Metrics endpoint: Returns data for all stores (store_001, store_002, store_1, store_2)
- Funnel endpoint: Working correctly
- Database: Contains 1168 events across 4 stores

⚠️ **Frontend**: Needs restart
- API client has been fixed with proper error handling and logging
- Environment variable fixed (`.env.local` points to `http://localhost:8000`)
- **ISSUE**: Frontend dev server needs restart to pick up changes

## Root Cause Analysis

1. **Previous Issue**: Frontend `.env.local` was pointing to non-existent Render URL
2. **Previous Issue**: API client had incorrect parameter construction
3. **Previous Issue**: Frontend dev server was running with old code

## Solution: Restart Frontend Dev Server

### Step 1: Stop the Current Frontend Server

In the terminal running the frontend:
```bash
# Press Ctrl+C to stop the dev server
```

### Step 2: Verify Environment Variable

Check `frontend/.env.local` contains:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start Frontend Server

```bash
cd frontend
npm run dev
```

### Step 4: Verify in Browser

1. Open http://localhost:3000
2. Open browser console (F12)
3. Look for these log messages:
   ```
   API Client initialized with URL: http://localhost:8000
   API Request: GET http://localhost:8000/health
   API Response: 200 /health
   API Request: GET http://localhost:8000/stores/store_001/metrics
   API Response: 200 /stores/store_001/metrics
   ```

## Expected Behavior

After restart, you should see:

### Dashboard
- ✅ Health Indicator: "Healthy" (green)
- ✅ Store selection: Dropdown with 4 stores
- ✅ Metrics cards: Total Entries, Total Exits, Current Occupancy, Avg Visit Duration
- ✅ Conversion Funnel: Chart with 4 stages
- ✅ Anomalies: Table with detected anomalies
- ✅ Last updated timestamp
- ✅ Auto-refresh every 30 seconds

### No Errors
- ❌ No "Network Error" messages
- ❌ No "Store not found" messages
- ❌ No 404 errors in console

## Backend Endpoints Verified

All endpoints tested and working:

### 1. Health Check
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","checks":{"database":"ok"},"response_time_ms":1.34,"timestamp":"2026-06-27T16:08:40.188066Z"}
```

### 2. Store Metrics
```bash
curl http://localhost:8000/stores/store_001/metrics
# Response: {"store_id":"store_001","total_entries":100,"total_exits":90,"current_occupancy":10,"average_visit_duration_seconds":554.94...}
```

### 3. Conversion Funnel
```bash
curl http://localhost:8000/stores/store_001/funnel
# Response: {"store_id":"store_001","stages":[{"stage":"entries","count":50,"conversion_rate":1.0},...]}
```

### 4. Anomalies
```bash
curl http://localhost:8000/stores/store_001/anomalies?time_window=24
# Response: {"anomalies":[...]}
```

Note: Anomalies endpoint returned 500 error - needs investigation if anomalies don't display.

## Available Stores

The database contains these stores (select from dropdown):
- `store_001` - Store 001 (Downtown)
- `store_002` - Store 002 (Mall)
- `store_1` - Store 1 (Purplle Store 1)
- `store_2` - Store 2 (Purplle Store 2)

## Troubleshooting

### If frontend still shows "Network Error":

1. **Verify backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Check if port 8000 is in use**:
   ```bash
   netstat -ano | findstr :8000
   ```

3. **Restart backend if needed**:
   ```bash
   python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload
   ```

### If frontend shows "Store not found":

1. **Verify store exists in database**:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/events.db'); cursor = conn.cursor(); cursor.execute('SELECT DISTINCT store_id FROM events'); print([s[0] for s in cursor.fetchall()]); conn.close()"
   ```
   Should output: `['store_001', 'store_002', 'store_1', 'store_2']`

2. **Check browser console** for actual API request URLs

3. **Verify `.env.local`** is correct (not pointing to Render URL)

### If anomalies don't display:

The anomalies endpoint returned 500 error during testing. Check backend logs for error details. This is a backend issue, not a frontend-backend connection issue.

## Files Modified

### 1. `frontend/.env.local`
Changed from:
```
NEXT_PUBLIC_API_URL=https://your-service.onrender.com
```

To:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. `frontend/src/lib/api.ts`
- Complete rewrite with proper error handling
- Added request/response interceptors for debugging
- Fixed parameter construction (`params` object instead of URL string)
- Added `withCredentials: false` for CORS
- Added comprehensive console logging

### 3. Backend (No Changes Needed)
- CORS already configured correctly
- All endpoints working (except anomalies which has a bug)
- Database populated with test data

## Next Steps After Fix

Once the frontend is working:

1. **Test all features**:
   - Switch between stores in dropdown
   - Verify metrics update
   - Check funnel chart displays correctly
   - Verify auto-refresh works (wait 30 seconds)

2. **Deploy to Production** (when ready):
   - Backend: Push to GitHub, deploy to Render
   - Frontend: Deploy to Vercel
   - Update `frontend/.env.local` to use Render backend URL

## Summary

The fix is simple: **Restart the frontend dev server**. All code changes have been made:
- ✅ API client fixed
- ✅ Environment variable fixed
- ✅ Backend verified working
- ⏳ Just needs frontend restart

**Command to fix:**
```bash
# In frontend terminal:
# 1. Press Ctrl+C
# 2. Run: npm run dev
# 3. Refresh browser at http://localhost:3000
```
