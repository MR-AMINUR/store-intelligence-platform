"""Test the anomalies API endpoint directly."""

import requests

try:
    print("Testing anomalies endpoint...")
    response = requests.get('http://localhost:8000/stores/store_001/anomalies?time_window=24')
    
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Success!")
        data = response.json()
        print(f"Found {len(data.get('anomalies', []))} anomalies")
    else:
        print(f"\n❌ Error: {response.status_code}")
        
        # Try to get more details from health endpoint
        health_response = requests.get('http://localhost:8000/health')
        print(f"\nHealth check: {health_response.status_code}")
        print(f"Health data: {health_response.json()}")
        
except Exception as e:
    print(f"❌ Request failed: {type(e).__name__}: {str(e)}")
