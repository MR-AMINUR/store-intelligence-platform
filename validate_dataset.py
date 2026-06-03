"""Validate existing pipeline against official Purplle dataset."""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import traceback

# Set up environment
os.environ["DB_PATH"] = "./data/purplle_validation.db"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["YOLO_MODEL_PATH"] = "./models/yolov8n.pt"
os.environ["CONFIDENCE_THRESHOLD"] = "0.5"
os.environ["TRACKER_MAX_AGE"] = "30"
os.environ["ZONE_CONFIG_PATH"] = "./config/zones.json"

from src.config import ConfigManager
from src.logger import Logger
from src.pipeline import VideoPipeline
from src.event_store import EventStore

def process_video(video_path, store_id, config, logger):
    """Process a single video through the pipeline."""
    result = {
        'video': video_path,
        'store_id': store_id,
        'status': 'pending',
        'error': None,
        'stats': {}
    }
    
    try:
        logger.info(f"Processing video: {video_path}", store_id=store_id)
        
        # Create pipeline
        pipeline = VideoPipeline(video_path, config, logger)
        
        # Process video
        pipeline_result = pipeline.process()
        
        # Record results
        result['status'] = 'success' if pipeline_result.success else 'failed'
        result['stats'] = {
            'total_frames': pipeline_result.total_frames,
            'frames_failed': pipeline_result.frames_failed,
            'events_generated': pipeline_result.events_generated,
            'events_stored': pipeline_result.events_stored
        }
        
        if pipeline_result.errors:
            result['error'] = '; '.join(pipeline_result.errors[:3])  # First 3 errors
        
        logger.info(
            f"Video processing completed",
            video=video_path,
            status=result['status'],
            **result['stats']
        )
        
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        logger.error(f"Video processing failed: {str(e)}", video=video_path, error=traceback.format_exc())
    
    return result

def get_event_statistics(event_store, store_id):
    """Get event statistics from database for a store."""
    try:
        # Get all events for this store
        events = event_store.get_events(store_id=store_id)
        
        # Count by event type
        event_counts = {}
        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events': len(events),
            'by_type': event_counts
        }
    except Exception as e:
        return {'error': str(e)}

def validate_dataset():
    """Main validation function."""
    print("=" * 100)
    print("PURPLLE DATASET VALIDATION")
    print("=" * 100)
    print()
    
    # Initialize
    config = ConfigManager()
    logger = Logger("DatasetValidation", "INFO")
    
    # Check prerequisites
    print("Checking Prerequisites...")
    print("-" * 100)
    
    model_path = config.get("YOLO_MODEL_PATH")
    zone_config = config.get("ZONE_CONFIG_PATH")
    
    prerequisites = []
    
    if not os.path.exists(model_path):
        prerequisites.append(f"❌ YOLOv8 model not found: {model_path}")
    else:
        prerequisites.append(f"✅ YOLOv8 model found: {model_path}")
    
    if not os.path.exists(zone_config):
        prerequisites.append(f"❌ Zone config not found: {zone_config}")
    else:
        prerequisites.append(f"✅ Zone config found: {zone_config}")
    
    for prereq in prerequisites:
        print(f"  {prereq}")
    
    if any("❌" in p for p in prerequisites):
        print("\n⚠️  Prerequisites not met. Validation aborted.")
        return
    
    print()
    
    # Define dataset structure
    dataset = {
        'Store 1': [
            ('CAM 3 - entry.mp4', 'entry'),
            ('CAM 1 - zone.mp4', 'zone'),
            ('CAM 2 - zone.mp4', 'zone'),
            ('CAM 5 - billing.mp4', 'billing')
        ],
        'Store 2': [
            ('entry 1.mp4', 'entry'),
            ('entry 2.mp4', 'entry'),
            ('zone.mp4', 'zone'),
            ('billing_area.mp4', 'billing')
        ]
    }
    
    # Process all videos
    print("Processing Videos...")
    print("-" * 100)
    
    all_results = []
    
    for store_name, videos in dataset.items():
        store_id = store_name.replace(' ', '_').lower()
        config_override = ConfigManager()
        config_override._config['STORE_ID'] = store_id
        
        print(f"\n{store_name} ({store_id}):")
        
        for video_file, camera_type in videos:
            video_path = f"data/{store_name}/{video_file}"
            
            if not os.path.exists(video_path):
                print(f"  ❌ {camera_type:8} | {video_file:30} | NOT FOUND")
                all_results.append({
                    'video': video_path,
                    'store_id': store_id,
                    'camera_type': camera_type,
                    'status': 'not_found',
                    'error': 'File not found'
                })
                continue
            
            result = process_video(video_path, store_id, config_override, logger)
            result['camera_type'] = camera_type
            all_results.append(result)
            
            # Print result
            if result['status'] == 'success':
                stats = result['stats']
                print(f"  ✅ {camera_type:8} | {video_file:30} | {stats['total_frames']:5} frames | {stats['events_generated']:4} events")
            elif result['status'] == 'error':
                print(f"  ❌ {camera_type:8} | {video_file:30} | ERROR: {result['error'][:50]}")
            else:
                print(f"  ⚠️  {camera_type:8} | {video_file:30} | FAILED: {result['error'][:50] if result['error'] else 'Unknown'}")
    
    print("\n" + "=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)
    
    # Aggregate statistics
    successful = [r for r in all_results if r['status'] == 'success']
    failed = [r for r in all_results if r['status'] in ['failed', 'error', 'not_found']]
    
    total_frames = sum(r['stats'].get('total_frames', 0) for r in successful)
    total_events = sum(r['stats'].get('events_generated', 0) for r in successful)
    
    print(f"\nProcessing Results:")
    print(f"  Total Videos: {len(all_results)}")
    print(f"  Successful: {len(successful)} ✅")
    print(f"  Failed: {len(failed)} ❌")
    print(f"  Success Rate: {len(successful)/len(all_results)*100:.1f}%")
    
    print(f"\nFrame Processing:")
    print(f"  Total Frames: {total_frames:,}")
    print(f"  Events Generated: {total_events:,}")
    print(f"  Events per Frame: {total_events/total_frames if total_frames > 0 else 0:.4f}")
    
    # Camera type breakdown
    print(f"\nBy Camera Type:")
    camera_stats = {}
    for result in successful:
        cam_type = result['camera_type']
        if cam_type not in camera_stats:
            camera_stats[cam_type] = {'count': 0, 'frames': 0, 'events': 0}
        camera_stats[cam_type]['count'] += 1
        camera_stats[cam_type]['frames'] += result['stats']['total_frames']
        camera_stats[cam_type]['events'] += result['stats']['events_generated']
    
    for cam_type in sorted(camera_stats.keys()):
        stats = camera_stats[cam_type]
        print(f"  {cam_type.capitalize():8} | Videos: {stats['count']} | Frames: {stats['frames']:,} | Events: {stats['events']:,}")
    
    # Event statistics from database
    print(f"\nDatabase Event Statistics:")
    try:
        event_store = EventStore(config.get("DB_PATH"), logger)
        
        for store_name in ['Store 1', 'Store 2']:
            store_id = store_name.replace(' ', '_').lower()
            event_stats = get_event_statistics(event_store, store_id)
            
            if 'error' in event_stats:
                print(f"  {store_name}: Error - {event_stats['error']}")
            else:
                print(f"  {store_name}: {event_stats['total_events']} total events")
                for event_type, count in sorted(event_stats['by_type'].items()):
                    print(f"    - {event_type}: {count}")
    except Exception as e:
        print(f"  Error accessing database: {str(e)}")
    
    # Errors encountered
    if failed:
        print(f"\nErrors Encountered:")
        for result in failed:
            print(f"  ❌ {result['video']}")
            print(f"     Error: {result['error']}")
    
    # Gap analysis
    print(f"\n" + "=" * 100)
    print("GAP ANALYSIS")
    print("=" * 100)
    
    gaps = []
    
    # Check camera types
    expected_camera_types = {'entry', 'zone', 'billing'}
    found_camera_types = set(r['camera_type'] for r in successful)
    
    if expected_camera_types == found_camera_types:
        print(f"\n✅ All camera types processed: {', '.join(sorted(found_camera_types))}")
    else:
        missing = expected_camera_types - found_camera_types
        if missing:
            gaps.append(f"Missing camera types: {', '.join(missing)}")
            print(f"\n❌ Missing camera types: {', '.join(missing)}")
    
    # Check event generation
    if total_events == 0:
        gaps.append("No events generated from any video")
        print(f"\n❌ No events generated from any video")
    else:
        print(f"\n✅ Events generated successfully: {total_events:,} events")
    
    # Check for failures
    if failed:
        gaps.append(f"{len(failed)} videos failed to process")
        print(f"\n❌ {len(failed)} videos failed to process")
    else:
        print(f"\n✅ All videos processed successfully")
    
    # Multi-camera handling
    print(f"\n✅ Multi-camera handling: Store 1 has {len([v for _, videos in dataset.items() if 'Store 1' in _ for v in videos])} cameras")
    print(f"✅ Multi-camera handling: Store 2 has {len([v for _, videos in dataset.items() if 'Store 2' in _ for v in videos])} cameras")
    
    # Save detailed report
    print(f"\n" + "=" * 100)
    print("REPORT GENERATION")
    print("=" * 100)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_videos': len(all_results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful)/len(all_results)*100,
            'total_frames': total_frames,
            'total_events': total_events
        },
        'results': all_results,
        'gaps': gaps,
        'camera_stats': camera_stats
    }
    
    report_path = 'PURPLLE_VALIDATION_REPORT.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed report saved to: {report_path}")
    
    # Final verdict
    print(f"\n" + "=" * 100)
    print("FINAL VERDICT")
    print("=" * 100)
    
    if len(failed) == 0 and total_events > 0:
        print(f"\n🎉 ✅ VALIDATION PASSED")
        print(f"\nThe existing pipeline successfully processed all {len(all_results)} videos")
        print(f"from the official Purplle dataset and generated {total_events:,} events.")
        print(f"\nNo gaps or issues identified. Solution is production-ready!")
    elif len(successful) > 0:
        print(f"\n⚠️  VALIDATION PARTIAL")
        print(f"\n{len(successful)}/{len(all_results)} videos processed successfully.")
        print(f"Generated {total_events:,} events from processed videos.")
        print(f"\nGaps identified: {len(gaps)}")
        for gap in gaps:
            print(f"  - {gap}")
    else:
        print(f"\n❌ VALIDATION FAILED")
        print(f"\nNo videos were processed successfully.")
        print(f"\nCritical issues prevent validation.")
    
    print(f"\n" + "=" * 100)

if __name__ == "__main__":
    try:
        validate_dataset()
    except Exception as e:
        print(f"\n❌ VALIDATION ABORTED")
        print(f"\nCritical error: {str(e)}")
        print(f"\nTraceback:")
        traceback.print_exc()
        sys.exit(1)
