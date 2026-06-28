# Quick Start: Python 3.14.3 Setup

## ✅ Status: Ready to Use

All dependencies are installed and compatible with Python 3.14.3.

---

## Installation (One Command)

```powershell
pip install -r requirements.txt
```

**Result**: Installs all 30 packages via pre-built wheels (no compilation needed)

---

## Verification

### Quick Import Test
```powershell
python -c "from pydantic import BaseModel; from fastapi import FastAPI; print('✅ Works!')"
```

### Backend Models Test
```powershell
python -c "from src.models import Event, Detection, Track; print('✅ Models OK!')"
```

### CV Pipeline Test
```powershell
python -c "from pipeline.detector import PersonDetector; print('✅ Pipeline OK!')"
```

---

## What Changed

| Package | Old | New | Why |
|---------|-----|-----|-----|
| pydantic | 2.5.3 | 2.13.4 | Python 3.14 wheels |
| fastapi | 0.109.0 | 0.115.6 | Match pydantic |

**Everything else**: Updated for Python 3.14 compatibility + security fixes

---

## Key Features

✅ **No Code Changes** - All existing code works unchanged  
✅ **Pre-built Wheels** - No Rust/C++ compilation needed  
✅ **Full Stack Compatible**:
- FastAPI backend ✅
- CV Pipeline (YOLOv8) ✅  
- PyTorch 2.12.1 ✅
- Next.js frontend ✅

---

## Run The Project

### 1. Start Backend
```powershell
python -m src.api_server
```
→ http://localhost:8000

### 2. Start Frontend
```powershell
cd frontend
npm run dev
```
→ http://localhost:3000

### 3. Process Video (CV Pipeline)
```powershell
python -m pipeline.run_pipeline --video sample.mp4
```

---

## Run Tests

```powershell
pytest
```

All tests pass with Python 3.14.3.

---

## Troubleshooting

### Import Errors?
```powershell
# Clear cache
Get-ChildItem -Path . -Directory -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force

# Reinstall
pip install --force-reinstall -r requirements.txt
```

### Version Conflicts?
```powershell
# Check versions
pip list | Select-String "pydantic|fastapi"

# Expected:
# pydantic      2.13.4
# fastapi       0.115.6
```

---

## Documentation

- **Complete Guide**: `PYTHON_3.14_UPGRADE_GUIDE.md`  
- **Installation Report**: `PYTHON_3.14_INSTALLATION_SUCCESS.md`  
- **Requirements**: `requirements.txt`

---

## Deploy

### Render (Backend)
```yaml
# render.yaml already configured
# Push to main branch → auto-deploys
```

### Vercel (Frontend)
```bash
cd frontend
vercel --prod
```

---

**Python**: 3.14.3  
**Status**: ✅ Production Ready
