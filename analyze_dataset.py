"""Analyze official Purplle dataset structure and metadata."""

import cv2
import os
from pathlib import Path

def get_video_metadata(video_path):
    """Extract metadata from video file."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return None
    
    metadata = {
        'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'size_mb': os.path.getsize(video_path) / (1024 * 1024)
    }
    
    cap.release()
    return metadata

def analyze_dataset():
    """Analyze the complete dataset structure."""
    data_dir = Path("data")
    
    results = {
        'Store 1': {},
        'Store 2': {}
    }
    
    # Analyze Store 1
    store1_dir = data_dir / "Store 1"
    if store1_dir.exists():
        for video_file in store1_dir.glob("*.mp4"):
            camera_type = video_file.stem.split(' - ')[-1] if ' - ' in video_file.stem else 'unknown'
            metadata = get_video_metadata(str(video_file))
            results['Store 1'][video_file.name] = {
                'type': camera_type,
                'metadata': metadata
            }
        
        # Check for layout
        layout_file = store1_dir / "Store 1 - layout.png"
        if layout_file.exists():
            results['Store 1']['layout'] = {
                'file': layout_file.name,
                'size_kb': os.path.getsize(layout_file) / 1024
            }
    
    # Analyze Store 2
    store2_dir = data_dir / "Store 2"
    if store2_dir.exists():
        for video_file in store2_dir.glob("*.mp4"):
            # Infer type from filename
            name_lower = video_file.stem.lower()
            if 'entry' in name_lower:
                camera_type = 'entry'
            elif 'billing' in name_lower:
                camera_type = 'billing'
            elif 'zone' in name_lower:
                camera_type = 'zone'
            else:
                camera_type = 'unknown'
            
            metadata = get_video_metadata(str(video_file))
            results['Store 2'][video_file.name] = {
                'type': camera_type,
                'metadata': metadata
            }
        
        # Check for layout
        layout_file = store2_dir / "store 2 - layout.png"
        if layout_file.exists():
            results['Store 2']['layout'] = {
                'file': layout_file.name,
                'size_kb': os.path.getsize(layout_file) / 1024
            }
    
    return results

if __name__ == "__main__":
    print("=" * 80)
    print("PURPLLE DATASET ANALYSIS")
    print("=" * 80)
    print()
    
    results = analyze_dataset()
    
    for store_name, store_data in results.items():
        print(f"\n{store_name}")
        print("-" * 80)
        
        # Separate videos and layout
        videos = {k: v for k, v in store_data.items() if k != 'layout'}
        layout = store_data.get('layout')
        
        # Group by camera type
        camera_types = {}
        for filename, data in videos.items():
            cam_type = data['type']
            if cam_type not in camera_types:
                camera_types[cam_type] = []
            camera_types[cam_type].append((filename, data['metadata']))
        
        # Print by camera type
        for cam_type in sorted(camera_types.keys()):
            print(f"\n  {cam_type.upper()} CAMERAS:")
            for filename, meta in camera_types[cam_type]:
                if meta:
                    print(f"    - {filename}")
                    print(f"      Frames: {meta['frames']:,} | FPS: {meta['fps']:.2f} | Duration: {meta['duration']:.1f}s")
                    print(f"      Resolution: {meta['width']}x{meta['height']} | Size: {meta['size_mb']:.1f} MB")
                else:
                    print(f"    - {filename} [ERROR: Could not read video]")
        
        # Print layout info
        if layout:
            print(f"\n  LAYOUT:")
            print(f"    - {layout['file']} ({layout['size_kb']:.1f} KB)")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_videos = 0
    total_duration = 0
    total_frames = 0
    
    for store_name, store_data in results.items():
        videos = {k: v for k, v in store_data.items() if k != 'layout'}
        store_videos = len(videos)
        store_duration = sum(v['metadata']['duration'] for v in videos.values() if v['metadata'])
        store_frames = sum(v['metadata']['frames'] for v in videos.values() if v['metadata'])
        
        print(f"\n{store_name}:")
        print(f"  Videos: {store_videos}")
        print(f"  Total Duration: {store_duration:.1f}s ({store_duration/60:.1f} minutes)")
        print(f"  Total Frames: {store_frames:,}")
        print(f"  Has Layout: {'Yes' if 'layout' in store_data else 'No'}")
        
        total_videos += store_videos
        total_duration += store_duration
        total_frames += store_frames
    
    print(f"\nOVERALL:")
    print(f"  Total Videos: {total_videos}")
    print(f"  Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    print(f"  Total Frames: {total_frames:,}")
    
    print("\n" + "=" * 80)
