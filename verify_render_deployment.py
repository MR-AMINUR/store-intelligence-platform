#!/usr/bin/env python3
"""
Verify that all files are ready for Render deployment.
This script checks prerequisites without modifying any files.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"  ✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"  ❌ {description}: {filepath} - NOT FOUND")
        return False

def check_file_executable(filepath):
    """Check if a file is executable (Unix/Linux)."""
    if os.name != 'nt':  # Not Windows
        if os.access(filepath, os.X_OK):
            print(f"  ✅ {filepath} is executable")
            return True
        else:
            print(f"  ⚠️  {filepath} is not executable (run: chmod +x {filepath})")
            return False
    else:
        print(f"  ℹ️  {filepath} executable check skipped (Windows)")
        return True

def verify_dockerfile():
    """Verify Dockerfile configuration."""
    print("\n📋 Checking Dockerfile...")
    
    if not check_file_exists("Dockerfile", "Dockerfile"):
        return False
    
    with open("Dockerfile", "r") as f:
        content = f.read()
        
        checks = {
            "EXPOSE 8000": "Port 8000 exposed",
            "HEALTHCHECK": "Health check configured",
            "CMD": "Start command defined",
            "ENTRYPOINT": "Entrypoint script configured",
            "python:3.10": "Python 3.10 base image"
        }
        
        all_good = True
        for keyword, description in checks.items():
            if keyword in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NOT FOUND")
                all_good = False
        
        return all_good

def verify_requirements():
    """Verify requirements.txt exists and has key dependencies."""
    print("\n📋 Checking requirements.txt...")
    
    if not check_file_exists("requirements.txt", "Python dependencies"):
        return False
    
    with open("requirements.txt", "r") as f:
        content = f.read().lower()
        
        required = ["fastapi", "uvicorn", "ultralytics", "opencv-python"]
        all_good = True
        
        for pkg in required:
            if pkg in content:
                print(f"  ✅ {pkg} listed")
            else:
                print(f"  ❌ {pkg} - NOT FOUND")
                all_good = False
        
        return all_good

def verify_model():
    """Verify YOLOv8 model exists."""
    print("\n📋 Checking YOLOv8 Model...")
    
    model_path = "models/yolov8n.pt"
    if check_file_exists(model_path, "YOLOv8n model"):
        size = os.path.getsize(model_path)
        if size > 5_000_000:  # Should be ~6.2 MB
            print(f"  ✅ Model size looks correct: {size:,} bytes")
            return True
        else:
            print(f"  ⚠️  Model size seems small: {size:,} bytes (expected ~6.2 MB)")
            return False
    return False

def verify_config():
    """Verify configuration files."""
    print("\n📋 Checking Configuration Files...")
    
    files = [
        ("config/zones.json", "Zone configuration"),
        ("init_db.py", "Database initialization script"),
        ("docker-entrypoint.sh", "Docker entrypoint script"),
        (".env.example", "Environment template")
    ]
    
    all_good = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    return all_good

def verify_render_files():
    """Verify Render-specific files."""
    print("\n📋 Checking Render Deployment Files...")
    
    files = [
        ("render.yaml", "Render blueprint"),
        (".env.render", "Render environment variables")
    ]
    
    all_good = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    return all_good

def verify_source_code():
    """Verify source code structure."""
    print("\n📋 Checking Source Code...")
    
    files = [
        "src/__init__.py",
        "src/api_server.py",
        "src/pipeline.py",
        "src/person_detector.py",
        "src/person_tracker.py",
        "src/event_generator.py",
        "src/event_store.py"
    ]
    
    all_good = True
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"  ❌ {filepath} - NOT FOUND")
            all_good = False
    
    if all_good:
        print(f"  ✅ All {len(files)} source files present")
    
    return all_good

def verify_environment_variables():
    """Check that .env.render has all required variables."""
    print("\n📋 Checking Environment Variables...")
    
    if not os.path.exists(".env.render"):
        print("  ❌ .env.render not found")
        return False
    
    with open(".env.render", "r") as f:
        content = f.read()
        
        required_vars = [
            "DB_PATH",
            "LOG_LEVEL",
            "YOLO_MODEL_PATH",
            "CONFIDENCE_THRESHOLD",
            "TRACKER_MAX_AGE",
            "ZONE_CONFIG_PATH",
            "STORE_ID"
        ]
        
        all_good = True
        for var in required_vars:
            if var in content:
                print(f"  ✅ {var} defined")
            else:
                print(f"  ❌ {var} - NOT FOUND")
                all_good = False
        
        return all_good

def main():
    """Main verification function."""
    print("=" * 70)
    print("RENDER DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print("\nChecking if all files are ready for Render deployment...")
    print("(No files will be modified)")
    
    results = {
        "Dockerfile": verify_dockerfile(),
        "Requirements": verify_requirements(),
        "Model": verify_model(),
        "Config Files": verify_config(),
        "Render Files": verify_render_files(),
        "Source Code": verify_source_code(),
        "Environment Variables": verify_environment_variables()
    }
    
    # Check docker-entrypoint.sh executable
    print("\n📋 Checking Script Permissions...")
    if os.path.exists("docker-entrypoint.sh"):
        check_file_executable("docker-entrypoint.sh")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for category, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {category}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ✅ ALL CHECKS PASSED!")
        print("\nYour project is ready for Render deployment.")
        print("\nNext steps:")
        print("  1. Push to GitHub: git push origin main")
        print("  2. Go to https://render.com")
        print("  3. Deploy with Blueprint (render.yaml)")
        print("\nSee RENDER_DEPLOYMENT_CHECKLIST.md for detailed steps.")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("\nPlease fix the issues above before deploying.")
        print("\nSee RENDER_DEPLOYMENT_GUIDE.md for help.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
