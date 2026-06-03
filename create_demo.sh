#!/bin/bash
# Create instant demo link using ngrok

echo "🚀 Creating Demo Link for Store Intelligence Platform"
echo "======================================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed"
    echo ""
    echo "Install ngrok:"
    echo "  1. Download from https://ngrok.com/download"
    echo "  2. Or run: brew install ngrok (Mac) or choco install ngrok (Windows)"
    echo ""
    exit 1
fi

echo "✅ ngrok found"
echo ""

# Start API server in background
echo "📦 Starting API server..."
uvicorn src.api_server:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for server to start
sleep 5

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API server running on http://localhost:8000"
else
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🌐 Creating public demo link with ngrok..."
echo ""

# Start ngrok
ngrok http 8000 --log=stdout &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get ngrok public URL
DEMO_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://.*')

if [ -z "$DEMO_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    kill $API_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 Demo Link Created!"
echo "======================================================"
echo ""
echo "🔗 Public Demo URL: $DEMO_URL"
echo ""
echo "📋 Available Endpoints:"
echo "  - API Docs:    $DEMO_URL/docs"
echo "  - Health:      $DEMO_URL/health"
echo "  - API Info:    $DEMO_URL/"
echo ""
echo "⚠️  This link is active as long as this script runs"
echo "⚠️  Press Ctrl+C to stop the demo"
echo ""
echo "======================================================"
echo ""

# Keep running
wait
