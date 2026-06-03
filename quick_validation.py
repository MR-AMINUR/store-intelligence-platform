"""Quick validation - process one video per store to verify system works."""

import os
import sys
from pathlib import Path

# Set up environment
os.environ["DB_PATH"] = "./data/quick_validation.db"
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log verbosity
os.environ["YOLO_MODEL_PATH"] = "./models/yolov8n.pt"
os.environ["CONFIDENCE_THRESHOLD"] = "0.5"
os.environ["TRACKER_MAX_AGE"] = "30"
os.environ["ZONE_CONFIG_PATH"] = "./config/zones.json"
os.environ["STORE_ID"] = "store_1"

from src.config import ConfigManager
from src.logger import Logger
from src.pipeline import VideoPipeline

def quick_validate():
    """Quick validation with one video per store."""
    print("=" * 100)
    print("QUICK VALIDATION - Official Purplle Dataset")
    print("=" * 100)
    print()
    
    # Initialize
    config = ConfigManager()
    logger = Logger("QuickValidation", "WARNING")
    
    # Check prerequisites
    model_path = config.get("YOLO_MODEL_PATH")
    if not os.path.exists(model_path):
        print(f"❌ YOLOv8 model not found: {model_path}")
        return
    
    print(f"✅ Model found: {model_path}")
    print()
    
    # Test one video per store
    test_videos = [
        ("data/Store 1/CAM 3 - entry.mp4", "store_1", "Store 1 - Entry Camera"),
        ("data/Store 2/entry 1.mp4", "store_2", "Store 2 - Entry Camera 1")
    ]
    
    results = []
    
    for video_path, store_id, description in test_videos:
        print(f"Processing: {description}")
        print(f"  Video: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"  ❌ File not found")
            results.append((description, False, 0, 0, "File not found"))
            continue
        
        try:
            # Update store ID
            config._config['STORE_ID'] = store_id
            
            # Create and run pipeline
            pipeline = VideoPipeline(video_path, config, logger)
            result = pipeline.process()
            
            if result.success:
                print(f"  ✅ Success")
                print(f"     Frames: {result.total_frames:,}")
                print(f"     Events: {result.events_generated}")
                results.append((description, True, result.total_frames, result.events_generated, None))
            else:
                print(f"  ❌ Failed: {result.errors[0] if result.errors else 'Unknown'}")
                results.append((description, False, 0, 0, result.errors[0] if result.errors else "Unknown"))
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append((description, False, 0, 0, str(e)))
        
        print()
    
    # Summary
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    successful = [r for r in results if r[1]]
    
    print(f"\nVideos Tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(results) - len(successful)}")
    
    if successful:
        total_frames = sum(r[2] for r in successful)
        total_events = sum(r[3] for r in successful)
        print(f"\nTotal Frames Processed: {total_frames:,}")
        print(f"Total Events Generated: {total_events}")
        print(f"Events per Frame: {total_events/total_frames:.4f}")
    
    print()
    
    if len(successful) == len(results):
        print("🎉 ✅ VALIDATION PASSED")
        print("\nThe existing pipeline successfully processes the official Purplle dataset!")
    elif len(successful) > 0:
        print("⚠️  VALIDATION PARTIAL")
        print(f"\n{len(successful)}/{len(results)} videos processed successfully.")
    else:
        print("❌ VALIDATION FAILED")
        print("\nNo videos were processed successfully.")
    
    print("=" * 100)

if __name__ == "__main__":
    try:
        quick_validate()
    except Exception as e:
        print(f"\n❌ VALIDATION ABORTED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
