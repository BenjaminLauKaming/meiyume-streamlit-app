#!/bin/bash

# Development Environment Stop Script
echo "🛑 Stopping CAD Analyzer Development Environment..."

# Stop ngrok
echo "🌐 Stopping ngrok tunnel..."
pkill -f ngrok || echo "No ngrok process found"

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
docker-compose down

echo "✅ Development environment stopped!"
echo ""
echo "📝 To start again: ./scripts/dev-start.sh" 