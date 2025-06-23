#!/bin/bash

# Production Environment Startup Script
echo "🚀 Starting CAD Analyzer Production Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create it from env_template.txt"
    echo "📝 Make sure to configure production settings:"
    echo "   • Set DEBUG=False"
    echo "   • Set strong SECRET_KEY"
    echo "   • Configure database credentials"
    echo "   • Set ALLOWED_HOSTS"
    echo "   • Configure AWS S3 for file storage"
    echo "   • Set up SSL certificates"
    exit 1
fi

# Verify production environment variables
source .env
if [ "$DEBUG" = "True" ]; then
    echo "❌ DEBUG is set to True! This is not safe for production."
    echo "📝 Please set DEBUG=False in your .env file"
    exit 1
fi

if [ "$SECRET_KEY" = "your-secret-key-here-generate-a-new-one" ]; then
    echo "❌ Default SECRET_KEY detected! Please generate a new secret key."
    echo "💡 You can generate one with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    exit 1
fi

# Create necessary directories
mkdir -p backend/logs
mkdir -p docker/nginx/certs
mkdir -p backups

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check for SSL certificates
if [ ! -f docker/nginx/certs/cert.pem ] || [ ! -f docker/nginx/certs/key.pem ]; then
    echo "⚠️  SSL certificates not found!"
    echo "🔒 Generating self-signed certificates for testing..."
    echo "   (Replace with real certificates for production!)"
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout docker/nginx/certs/key.pem \
        -out docker/nginx/certs/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Create backup before deployment
echo "💾 Creating database backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
if docker ps -q -f name=cad_analyzer_db_prod; then
    docker exec cad_analyzer_db_prod pg_dump -U $POSTGRES_USER $POSTGRES_DB > backups/backup_$timestamp.sql
    echo "✅ Backup created: backups/backup_$timestamp.sql"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Build and start production environment
echo "🏗️  Building and starting production environment..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 15

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput

# Create superuser if needed
echo "👤 Checking for Django superuser..."
docker-compose -f docker-compose.prod.yml exec django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Please create one manually:')
    print('docker-compose -f docker-compose.prod.yml exec django python manage.py createsuperuser')
else:
    print('Superuser exists')
"

# Health check
echo "🏥 Performing health checks..."
sleep 5

# Check if services are responding
services=("django:8000" "streamlit:8501" "n8n:5678")
for service in "${services[@]}"; do
    container=${service%:*}
    if docker-compose -f docker-compose.prod.yml ps -q $container > /dev/null; then
        echo "✅ $container service is running"
    else
        echo "❌ $container service failed to start"
    fi
done

echo ""
echo "🎉 Production environment deployed!"
echo ""
echo "🌐 Services available at:"
echo "   • Main Application: https://localhost (or your domain)"
echo "   • Django Admin: https://localhost/admin"
echo "   • n8n Workflows: https://localhost/n8n"
echo ""
echo "🔍 Monitoring commands:"
echo "   • View logs: docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "   • Check status: docker-compose -f docker-compose.prod.yml ps"
echo "   • Stop services: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "📊 Database backup created at: backups/backup_$timestamp.sql"
echo ""
echo "⚠️  Important:"
echo "   • Replace self-signed SSL certificates with real ones"
echo "   • Set up proper monitoring and alerting"
echo "   • Configure regular database backups"
echo "   • Review security settings" 