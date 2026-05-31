#!/usr/bin/env python3
"""Verification script to check if the project setup is complete."""

import sys
import os
from pathlib import Path


def check_directory_structure():
    """Check if all required directories exist."""
    print("Checking directory structure...")
    required_dirs = ["src", "tests", "config", "data", "models"]
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)
            print(f"  ❌ Missing directory: {dir_name}")
        else:
            print(f"  ✓ Directory exists: {dir_name}")
    
    return len(missing_dirs) == 0


def check_required_files():
    """Check if all required files exist."""
    print("\nChecking required files...")
    required_files = [
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "pytest.ini",
        "mypy.ini",
        "setup.py",
        "README.md",
        "SETUP_GUIDE.md",
    ]
    missing_files = []
    
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
            print(f"  ❌ Missing file: {file_name}")
        else:
            print(f"  ✓ File exists: {file_name}")
    
    return len(missing_files) == 0


def check_python_version():
    """Check if Python version is 3.10 or higher."""
    print("\nChecking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (Requires 3.10+)")
        return False


def check_virtual_environment():
    """Check if running in a virtual environment."""
    print("\nChecking virtual environment...")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print(f"  ✓ Running in virtual environment: {sys.prefix}")
        return True
    else:
        print("  ⚠ Not running in a virtual environment (recommended)")
        return False


def check_dependencies():
    """Check if key dependencies can be imported."""
    print("\nChecking dependencies...")
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("pydantic", "Pydantic"),
        ("pytest", "Pytest"),
        ("hypothesis", "Hypothesis"),
    ]
    
    missing_deps = []
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name} installed")
        except ImportError:
            missing_deps.append(display_name)
            print(f"  ❌ {display_name} not installed")
    
    if missing_deps:
        print(f"\n  Run: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Store Intelligence Platform - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure()),
        ("Required Files", check_required_files()),
        ("Python Version", check_python_version()),
        ("Virtual Environment", check_virtual_environment()),
    ]
    
    # Only check dependencies if basic structure is OK
    if all(result for _, result in checks):
        checks.append(("Dependencies", check_dependencies()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in checks:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! Setup is complete.")
        print("\nNext steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Create config/zones.json with zone definitions")
        print("  3. Run tests: pytest tests/ -v")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the output above.")
        print("\nRefer to SETUP_GUIDE.md for detailed setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
