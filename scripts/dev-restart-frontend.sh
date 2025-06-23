#!/bin/bash

# Quick restart for frontend development
echo "🔄 Restarting Streamlit frontend..."

docker-compose restart streamlit

echo "✅ Streamlit restarted!"
echo "🌐 Frontend available at: http://localhost:8501"

# Show logs for debugging
echo "📊 Showing logs (Ctrl+C to stop):"
docker-compose logs -f streamlit 