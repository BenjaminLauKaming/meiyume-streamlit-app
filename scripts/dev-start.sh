#!/bin/bash

# Development Environment Startup Script
echo "🚀 Starting CAD Analyzer Development Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env_template.txt .env
    echo "⚠️  Please edit .env file with your configuration before continuing!"
    echo "📝 At minimum, set your GOOGLE_GEMINI_API_KEY"
    exit 1
fi

# Create necessary directories
mkdir -p backend/logs
mkdir -p media
mkdir -p staticfiles

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start development environment
echo "🏗️  Building and starting development environment..."
docker-compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec django python manage.py migrate

# Create superuser (if not exists)
echo "👤 Creating Django superuser..."
docker-compose exec django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start ngrok for external access
echo "🌐 Starting ngrok tunnel..."
if command -v ngrok >/dev/null 2>&1; then
    # Kill any existing ngrok processes
    pkill -f ngrok || true
    
    # Start ngrok in background
    ngrok http 8000 > /dev/null 2>&1 &
    NGROK_PID=$!
    
    # Wait for ngrok to start
    sleep 3
    
    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('Failed to get ngrok URL')
")
    
    echo "✅ ngrok tunnel started (PID: $NGROK_PID)"
    echo "🌐 Public URL: $NGROK_URL"
else
    echo "⚠️  ngrok not found. Install with: brew install ngrok"
    echo "   Or download from: https://ngrok.com/download"
fi

# Show running services
echo "✅ Development environment is ready!"
echo ""
echo "🌐 Services available at:"
echo "   • Streamlit Frontend: http://localhost:8501"
echo "   • Django API: http://localhost:8000"
echo "   • Django Admin: http://localhost:8000/admin (admin/admin123)"
echo "   • n8n Workflows: http://localhost:5678 (admin/admin123)"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo "   • ngrok Dashboard: http://localhost:4040"
if [ ! -z "$NGROK_URL" ]; then
    echo "   • Public API: $NGROK_URL"
    echo "   • Webhook URL: $NGROK_URL/api/cad/webhook/n8n-callback/"
fi
echo ""
echo "📊 To view logs: docker-compose logs -f [service_name]"
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart ngrok: pkill -f ngrok && ngrok http 8000" 