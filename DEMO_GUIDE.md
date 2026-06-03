# Demo Guide - Store Intelligence Platform

**Purpose**: Create a live demo link for the Purplle Store Intelligence Platform  
**Audience**: Reviewers, stakeholders, technical evaluators

---

## 🎯 Demo Options

### Option 1: Instant Demo with Ngrok (5 Minutes) ⭐ **RECOMMENDED**

Create a public demo link instantly without deployment:

#### Windows
```bash
# 1. Install ngrok (if not installed)
choco install ngrok
# OR download from https://ngrok.com/download

# 2. Run demo script
create_demo.bat
```

#### Mac/Linux
```bash
# 1. Install ngrok (if not installed)
brew install ngrok

# 2. Run demo script
chmod +x create_demo.sh
./create_demo.sh
```

**Result**: You'll get a public URL like `https://xxxx.ngrok-free.app`

**Pros**:
- ✅ Instant (5 minutes)
- ✅ No cloud account needed
- ✅ Free
- ✅ Works with local database

**Cons**:
- ⚠️ Link expires when you stop the script
- ⚠️ Requires your computer to stay on

---

### Option 2: Deploy to Railway (15 Minutes)

Deploy to Railway for a permanent demo link:

```bash
# 1. Sign up at https://railway.app (free)

# 2. Install Railway CLI
npm install -g @railway/cli

# 3. Login
railway login

# 4. Initialize project
railway init

# 5. Deploy
railway up

# 6. Add domain (optional)
railway domain
```

**Result**: You'll get a URL like `https://store-intelligence-production.up.railway.app`

**Pros**:
- ✅ Permanent link
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy deployment

**Cons**:
- ⏱️ Takes 15 minutes
- ⚠️ Requires Railway account

---

### Option 3: Deploy to Render (20 Minutes)

Deploy to Render for production-quality demo:

1. **Sign up**: https://render.com (free)
2. **New Web Service**: Click "New +" → "Web Service"
3. **Connect GitHub**: Link your repository
4. **Configure**:
   - Name: `store-intelligence-platform`
   - Environment: Docker
   - Plan: Free
5. **Deploy**: Render will auto-deploy

**Result**: You'll get a URL like `https://store-intelligence.onrender.com`

**Pros**:
- ✅ Production-quality hosting
- ✅ Automatic deployments (git push)
- ✅ Free SSL
- ✅ Always online

**Cons**:
- ⏱️ Takes 20 minutes
- ⚠️ Free tier may have cold starts

---

### Option 4: Video Demo (Alternative)

Create a video demo showing the platform in action:

```bash
# 1. Start API server
uvicorn src.api_server:app --reload

# 2. Record screen showing:
#    - API documentation (/docs)
#    - Processing a video
#    - Viewing events in database
#    - Querying analytics endpoints

# 3. Upload to:
#    - YouTube (unlisted)
#    - Loom
#    - Google Drive
```

**Tools**: OBS Studio, Loom, QuickTime (Mac), Xbox Game Bar (Windows)

---

## 📋 Demo Checklist

### Before Creating Demo

- [ ] All tests passing: `pytest tests/ -v`
- [ ] API server working: `uvicorn src.api_server:app`
- [ ] Health endpoint responding: `curl http://localhost:8000/health`
- [ ] Sample data available (optional): Process one video first

### Demo Content to Show

1. **API Documentation** (`/docs`)
   - Interactive Swagger UI
   - All 7 endpoints visible
   - Try out feature working

2. **Health Check** (`/health`)
   - System status
   - Database connectivity

3. **Event Ingestion** (`POST /events/ingest`)
   - Single event
   - Batch events

4. **Analytics** (various endpoints)
   - Store metrics
   - Conversion funnel
   - Spatial heatmap
   - Anomaly detection

5. **OpenAPI Schema** (`/openapi.json`)
   - Complete API specification

---

## 🚀 Quick Demo Setup (Ngrok)

### Step-by-Step

#### 1. Install Prerequisites
```bash
# Python dependencies
pip install -r requirements.txt

# Ngrok (choose your platform)
# Windows (with Chocolatey):
choco install ngrok

# Mac:
brew install ngrok

# Linux:
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

#### 2. Start API Server
```bash
# Terminal 1: Start API
uvicorn src.api_server:app --host 0.0.0.0 --port 8000

# Verify it's running
curl http://localhost:8000/health
```

#### 3. Create Public Tunnel
```bash
# Terminal 2: Start ngrok
ngrok http 8000

# You'll see output like:
# Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

#### 4. Share Your Demo Link
```
Your demo link: https://abc123.ngrok-free.app

Available at:
- API Docs:    https://abc123.ngrok-free.app/docs
- Health:      https://abc123.ngrok-free.app/health
- API Info:    https://abc123.ngrok-free.app/
```

---

## 🎬 Demo Script

Use this script when presenting your demo:

### Introduction (1 minute)
```
"This is the Store Intelligence Platform - a computer vision system 
that processes retail video footage to generate actionable analytics."

Show: Landing page at https://your-demo-url.com/
```

### API Documentation (2 minutes)
```
"The platform exposes 7 REST API endpoints. Let me show you the 
interactive documentation."

Show: https://your-demo-url.com/docs

Highlight:
- Event ingestion endpoint
- Analytics endpoints (metrics, funnel, heatmap, anomalies)
- Health check
```

### Live Demo - Event Ingestion (2 minutes)
```
"Let's ingest a sample event in real-time."

Action:
1. Open /docs
2. Click POST /events/ingest
3. Click "Try it out"
4. Paste sample event JSON:
{
  "event_id": "demo-event-001",
  "event_type": "ENTRY",
  "track_id": 1,
  "timestamp": "2024-01-01T10:00:00Z",
  "store_id": "store_001",
  "frame_number": 100,
  "position": {"x": 100, "y": 200},
  "metadata": {}
}
5. Click "Execute"
6. Show 201 response
```

### Live Demo - Analytics (2 minutes)
```
"Now let's query the analytics. We can get store metrics like 
entry/exit counts, occupancy, and visit duration."

Action:
1. Click GET /stores/{id}/metrics
2. Try it out with store_id = "store_001"
3. Show metrics response
```

### Architecture (1 minute)
```
"The system uses YOLOv8 for person detection, ByteTrack for tracking,
and generates 8 different event types. It's fully containerized with
Docker and includes 95% test coverage."

Show: Architecture diagram from DESIGN.md
```

### Validation Results (1 minute)
```
"We've validated this with the official Purplle dataset. 
The system successfully processed real retail footage and 
generated 162 events with zero errors."

Show: PURPLLE_DATASET_VALIDATION_REPORT.md (summary section)
```

---

## 📊 Demo Data

### Sample Events for Testing

```json
[
  {
    "event_id": "demo-entry-001",
    "event_type": "ENTRY",
    "track_id": 1,
    "timestamp": "2024-01-01T10:00:00Z",
    "store_id": "store_001",
    "frame_number": 100,
    "position": {"x": 100, "y": 200},
    "metadata": {}
  },
  {
    "event_id": "demo-zone-enter-001",
    "event_type": "ZONE_ENTER",
    "track_id": 1,
    "timestamp": "2024-01-01T10:00:05Z",
    "store_id": "store_001",
    "frame_number": 250,
    "position": {"x": 300, "y": 400},
    "metadata": {"zone_id": "electronics", "zone_name": "Electronics Section"}
  },
  {
    "event_id": "demo-exit-001",
    "event_type": "EXIT",
    "track_id": 1,
    "timestamp": "2024-01-01T10:05:00Z",
    "store_id": "store_001",
    "frame_number": 9100,
    "position": {"x": 150, "y": 250},
    "metadata": {}
  }
]
```

### cURL Commands for Demo

```bash
# Health check
curl https://your-demo-url.com/health

# Ingest single event
curl -X POST https://your-demo-url.com/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "demo-001",
    "event_type": "ENTRY",
    "track_id": 1,
    "timestamp": "2024-01-01T10:00:00Z",
    "store_id": "store_001",
    "frame_number": 100,
    "position": {"x": 100, "y": 200},
    "metadata": {}
  }'

# Get store metrics
curl https://your-demo-url.com/stores/store_001/metrics

# Get conversion funnel
curl https://your-demo-url.com/stores/store_001/funnel

# Get heatmap
curl https://your-demo-url.com/stores/store_001/heatmap?resolution=20

# Get anomalies
curl https://your-demo-url.com/stores/store_001/anomalies?window_minutes=60
```

---

## 🔧 Troubleshooting

### Ngrok Issues

**Problem**: "command not found: ngrok"
```bash
# Solution: Install ngrok
# Windows: choco install ngrok
# Mac: brew install ngrok
# Linux: See installation steps above
```

**Problem**: "Tunnel established, but can't access URL"
```bash
# Solution: Check firewall
# Windows: Allow Python in Windows Firewall
# Mac: System Preferences > Security > Allow
```

**Problem**: "429 Too Many Requests"
```bash
# Solution: Sign up for free ngrok account
ngrok authtoken YOUR_AUTH_TOKEN
# Get token from https://dashboard.ngrok.com/get-started/your-authtoken
```

### API Server Issues

**Problem**: "Port 8000 already in use"
```bash
# Solution: Use different port
uvicorn src.api_server:app --port 8001

# Update ngrok command
ngrok http 8001
```

**Problem**: "Database locked"
```bash
# Solution: Restart API server
# Ctrl+C to stop
# Re-run uvicorn command
```

---

## 📝 Demo URLs to Share

### What to Include in Your Submission

```
Demo Link: https://your-demo-url.com

Quick Links:
- API Documentation:  https://your-demo-url.com/docs
- Health Check:       https://your-demo-url.com/health
- OpenAPI Schema:     https://your-demo-url.com/openapi.json

Test Credentials: None required (public API)

Sample Request:
curl https://your-demo-url.com/stores/store_001/metrics

Note: Demo link is active 24/7 (if deployed to Railway/Render)
      OR active during evaluation period (if using ngrok)
```

---

## 🎥 Video Demo Alternative

If you prefer a video demo:

### Recording Checklist

- [ ] Record in 1080p
- [ ] Show desktop clearly (no personal info)
- [ ] Enable microphone (explain what you're doing)
- [ ] Keep video under 10 minutes
- [ ] Show:
  - [ ] Starting the application
  - [ ] API documentation (/docs)
  - [ ] Making API calls
  - [ ] Viewing responses
  - [ ] Running tests
  - [ ] Docker deployment

### Recording Tools

**Windows**: 
- Xbox Game Bar (built-in, Win+G)
- OBS Studio (free, https://obsproject.com)

**Mac**:
- QuickTime Player (built-in)
- OBS Studio (free)

**Online**:
- Loom (https://loom.com) - Free for up to 5 min
- Screencast-O-Matic

### Upload Options

1. **YouTube** (unlisted): https://youtube.com/upload
2. **Loom**: https://loom.com (generates instant link)
3. **Google Drive**: Upload and get shareable link
4. **Dropbox**: Upload and create shared link

---

## ✅ Demo Checklist

Before sharing your demo link:

- [ ] API is accessible from demo URL
- [ ] `/docs` endpoint shows interactive documentation
- [ ] `/health` endpoint returns healthy status
- [ ] Sample API calls work correctly
- [ ] No errors in server logs
- [ ] Demo link is included in submission
- [ ] Demo stays online during evaluation period

---

## 🎯 Demo Best Practices

1. **Keep It Simple**: Focus on core functionality
2. **Show Real Data**: Use the Purplle dataset validation as proof
3. **Be Available**: Keep demo running during evaluation
4. **Provide Context**: Include this guide with your submission
5. **Test First**: Verify demo works before sharing

---

**Created**: 2024-06-03  
**Status**: Ready for Demo Creation  
**Estimated Setup Time**: 5-20 minutes (depending on method)
