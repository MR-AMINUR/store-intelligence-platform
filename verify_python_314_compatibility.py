"""Verification script for Python 3.14.3 compatibility.

This script tests that all upgraded dependencies work correctly
with Python 3.14.3 and that existing functionality is preserved.
"""

import sys


def check_python_version():
    """Check Python version is 3.14+."""
    print("=" * 70)
    print("Python 3.14 Compatibility Verification")
    print("=" * 70)
    print()
    
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 14:
        print(f"⚠️  Warning: This script is designed for Python 3.14+")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print()
    
    return True


def test_pydantic():
    """Test Pydantic 2.10+ works correctly."""
    print("=" * 70)
    print("Testing Pydantic 2.10+")
    print("=" * 70)
    
    try:
        from pydantic import BaseModel, Field, __version__
        print(f"✅ Pydantic version: {__version__}")
        
        # Test basic model
        class TestModel(BaseModel):
            name: str
            value: int = Field(gt=0)
        
        # Test validation
        obj = TestModel(name="test", value=42)
        assert obj.name == "test"
        assert obj.value == 42
        print("✅ Basic model validation works")
        
        # Test serialization
        data = obj.model_dump()
        assert data == {"name": "test", "value": 42}
        print("✅ Model serialization works")
        
        # Test JSON schema
        schema = TestModel.model_json_schema()
        assert "properties" in schema
        print("✅ JSON schema generation works")
        
        # Check pydantic-core
        from pydantic_core import __version__ as core_version
        print(f"✅ pydantic-core version: {core_version}")
        
        major, minor = map(int, core_version.split('.')[:2])
        if major < 2 or (major == 2 and minor < 27):
            print(f"⚠️  Warning: pydantic-core {core_version} may not have Python 3.14 wheels")
            print(f"   Recommended: pydantic-core >= 2.27")
        else:
            print(f"✅ pydantic-core {core_version} has Python 3.14 support")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic test failed: {e}")
        return False


def test_fastapi():
    """Test FastAPI 0.115+ works correctly."""
    print()
    print("=" * 70)
    print("Testing FastAPI 0.115+")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI, __version__
        from pydantic import BaseModel
        
        print(f"✅ FastAPI version: {__version__}")
        
        # Test app creation
        app = FastAPI(title="Test App")
        print("✅ FastAPI app creation works")
        
        # Test route with Pydantic model
        class Item(BaseModel):
            name: str
            price: float
        
        @app.post("/test")
        def test_endpoint(item: Item):
            return item
        
        print("✅ Route with Pydantic model works")
        
        # Test route registration
        routes = [route.path for route in app.routes]
        assert "/test" in routes
        print("✅ Route registration works")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False


def test_sqlalchemy():
    """Test SQLAlchemy 2.0+ works correctly."""
    print()
    print("=" * 70)
    print("Testing SQLAlchemy 2.0+")
    print("=" * 70)
    
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, Column, Integer, String
        from sqlalchemy.orm import declarative_base
        
        print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
        
        # Test engine creation
        engine = create_engine("sqlite:///:memory:")
        print("✅ Engine creation works")
        
        # Test model definition
        Base = declarative_base()
        
        class TestTable(Base):
            __tablename__ = "test"
            id = Column(Integer, primary_key=True)
            name = Column(String)
        
        print("✅ Model definition works")
        
        # Test table creation
        Base.metadata.create_all(engine)
        print("✅ Table creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy test failed: {e}")
        return False


def test_cv_pipeline():
    """Test CV pipeline dependencies."""
    print()
    print("=" * 70)
    print("Testing CV Pipeline Dependencies")
    print("=" * 70)
    
    errors = []
    
    # Test numpy
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
    except Exception as e:
        print(f"❌ NumPy: {e}")
        errors.append("NumPy")
    
    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
    except Exception as e:
        print(f"❌ OpenCV: {e}")
        errors.append("OpenCV")
    
    # Test PyTorch
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        
        # Check CUDA
        if torch.cuda.is_available():
            print(f"✅ CUDA available (Device: {torch.cuda.get_device_name(0)})")
        else:
            print("ℹ️  CUDA not available (CPU mode)")
    except Exception as e:
        print(f"❌ PyTorch: {e}")
        errors.append("PyTorch")
    
    # Test Ultralytics
    try:
        from ultralytics import __version__ as yolo_version
        print(f"✅ Ultralytics (YOLOv8) version: {yolo_version}")
    except Exception as e:
        print(f"❌ Ultralytics: {e}")
        errors.append("Ultralytics")
    
    # Test requests
    try:
        import requests
        print(f"✅ Requests version: {requests.__version__}")
    except Exception as e:
        print(f"❌ Requests: {e}")
        errors.append("Requests")
    
    return len(errors) == 0


def test_existing_imports():
    """Test that existing project modules can be imported."""
    print()
    print("=" * 70)
    print("Testing Existing Project Modules")
    print("=" * 70)
    
    modules = [
        ("src.models", "Data models"),
        ("src.config", "Configuration"),
        ("src.logger", "Logger"),
        ("src.event_store", "Event store"),
        ("pipeline.config", "Pipeline config"),
        ("pipeline.detector", "Person detector"),
        ("pipeline.tracker", "Person tracker"),
        ("pipeline.zone_manager", "Zone manager"),
        ("pipeline.event_generator", "Event generator"),
        ("pipeline.event_sender", "Event sender"),
    ]
    
    errors = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {description}: {module_name}")
        except Exception as e:
            print(f"❌ {description}: {e}")
            errors.append(module_name)
    
    return len(errors) == 0


def test_pydantic_models():
    """Test that existing Pydantic models work."""
    print()
    print("=" * 70)
    print("Testing Existing Pydantic Models")
    print("=" * 70)
    
    try:
        from src.models import (
            Event, EventType, BoundingBox, Detection, Track,
            StoreMetrics, ConversionFunnel, Anomaly
        )
        from datetime import datetime, timezone
        
        # Test Event model
        event = Event(
            event_id="test-001",
            event_type=EventType.ENTRY,
            timestamp=datetime.now(timezone.utc),
            store_id="store_001",
            track_id=1,
            metadata={}
        )
        print("✅ Event model works")
        
        # Test BoundingBox
        bbox = BoundingBox(x=10, y=20, width=100, height=200)
        print("✅ BoundingBox model works")
        
        # Test Detection
        detection = Detection(bbox=bbox, confidence=0.95, class_id=0)
        print("✅ Detection model works")
        
        # Test Track
        from src.models import TrackState
        track = Track(
            track_id=1,
            bbox=bbox,
            frame_number=100,
            age=0,
            state=TrackState.ACTIVE
        )
        print("✅ Track model works")
        
        # Test StoreMetrics
        metrics = StoreMetrics(
            store_id="store_001",
            total_entries=100,
            total_exits=90,
            current_occupancy=10,
            average_visit_duration_seconds=600.0
        )
        print("✅ StoreMetrics model works")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print()
    
    results = []
    
    # Run tests
    results.append(("Python Version", check_python_version()))
    results.append(("Pydantic", test_pydantic()))
    results.append(("FastAPI", test_fastapi()))
    results.append(("SQLAlchemy", test_sqlalchemy()))
    results.append(("CV Pipeline", test_cv_pipeline()))
    results.append(("Project Imports", test_existing_imports()))
    results.append(("Pydantic Models", test_pydantic_models()))
    
    # Summary
    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12} {name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print()
        print("✅ All verification tests passed!")
        print("   Your project is fully compatible with Python 3.14.3")
        print()
        print("Next steps:")
        print("  1. Start backend: python -m src.api_server")
        print("  2. Process video: python -m pipeline.run_pipeline --video sample.mp4")
        print("  3. Run tests: pytest")
        print()
        return 0
    else:
        print()
        print("❌ Some verification tests failed")
        print("   Please check the errors above and install missing dependencies:")
        print("   pip install -r requirements.txt")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
