"""Test script to verify pipeline installation.

This script checks if all pipeline dependencies are installed correctly
and if the modules can be imported without errors.
"""

import sys


def test_imports():
    """Test importing all pipeline modules."""
    print("=" * 70)
    print("Testing Pipeline Installation")
    print("=" * 70)
    print()
    
    errors = []
    
    # Test core dependencies
    print("✓ Checking core dependencies...")
    dependencies = [
        ("numpy", "NumPy"),
        ("cv2", "OpenCV"),
        ("torch", "PyTorch"),
        ("ultralytics", "Ultralytics (YOLOv8)"),
        ("requests", "Requests"),
    ]
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name}: {e}")
            errors.append(f"{display_name} not installed")
    
    print()
    
    # Test pipeline modules
    print("✓ Checking pipeline modules...")
    modules = [
        ("pipeline.config", "Configuration"),
        ("pipeline.detector", "Detector"),
        ("pipeline.tracker", "Tracker"),
        ("pipeline.zone_manager", "Zone Manager"),
        ("pipeline.event_generator", "Event Generator"),
        ("pipeline.event_sender", "Event Sender"),
        ("pipeline.video_processor", "Video Processor"),
        ("pipeline.run_pipeline", "Pipeline Orchestrator"),
    ]
    
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name}: {e}")
            errors.append(f"{display_name} module cannot be imported")
    
    print()
    
    # Test CUDA availability
    print("✓ Checking GPU support...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✅ CUDA available (Device: {torch.cuda.get_device_name(0)})")
        else:
            print("  ⚠️  CUDA not available (will use CPU)")
    except Exception as e:
        print(f"  ❌ Error checking CUDA: {e}")
    
    print()
    
    # Test configuration files
    print("✓ Checking configuration files...")
    from pathlib import Path
    
    config_files = [
        ("config/zones.json", "Zone configuration"),
        ("models/yolov8n.pt", "YOLOv8 model (optional)"),
        ("pipeline_config.json", "Pipeline configuration (optional)"),
    ]
    
    for file_path, description in config_files:
        if Path(file_path).exists():
            print(f"  ✅ {description}: {file_path}")
        else:
            if "optional" in description:
                print(f"  ⚠️  {description}: {file_path} (not found, but optional)")
            else:
                print(f"  ❌ {description}: {file_path} (not found)")
                errors.append(f"{description} not found at {file_path}")
    
    print()
    
    # Summary
    print("=" * 70)
    if not errors:
        print("✅ All checks passed! Pipeline is ready to use.")
        print()
        print("Next steps:")
        print("  1. Download YOLOv8 model (if not already downloaded):")
        print("     wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt")
        print()
        print("  2. Start backend server:")
        print("     python -m src.api_server")
        print()
        print("  3. Process a video:")
        print("     python -m pipeline.run_pipeline --video sample.mp4")
        print("=" * 70)
        return True
    else:
        print("❌ Installation incomplete. Please fix the following issues:")
        print()
        for error in errors:
            print(f"  - {error}")
        print()
        print("Install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("=" * 70)
        return False


def main():
    """Main entry point."""
    success = test_imports()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
