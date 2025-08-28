#!/bin/bash

# Production Environment Startup Script
echo "🚀 Starting Meiyume AI Assistant Production Environment..."

# Check if .env.prod file exists
if [ ! -f .env.prod ]; then
    echo "📋 Creating .env.prod from template..."
    cp env_template.txt .env.prod
    
    echo ""
    echo "📝 Production Configuration Guide:"
    echo "Please update .env.prod with these production settings:"
    echo ""
    echo "Required changes in .env.prod:"
    echo "1. ENVIRONMENT=production"
    echo "2. DEBUG=False"
    echo "3. DJANGO_SETTINGS_MODULE=ai_cad_analyzer.settings.production"
    echo "4. Set strong SECRET_KEY (generate new one)"
    echo "5. Set ALLOWED_HOSTS=yourdomain.com,localhost"
    echo "6. Configure PostgreSQL production database"
    echo "7. Set REDIS_PASSWORD for security"
    echo ""
    echo "Optional (for real production):"
    echo "8. Configure AWS S3 settings"
    echo "9. Set up email settings"
    echo "10. Configure Sentry for monitoring"
    echo ""
    echo "⚠️  For this demo, you can keep most default values"
    echo "✏️  Edit .env.prod manually, then run this script again"
    echo ""
    echo "💡 To generate a new SECRET_KEY, run:"
    echo "   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    echo ""
    exit 1
fi

# Copy .env.prod to .env for docker-compose
cp .env.prod .env

# Verify production environment variables
source .env
if [ "$DEBUG" = "True" ]; then
    echo "❌ DEBUG is set to True! This is not safe for production."
    echo "📝 Please set DEBUG=False in your .env.prod file"
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
if docker ps -q -f name=meiyume_ai_assistant_db_prod; then
    docker exec meiyume_ai_assistant_db_prod pg_dump -U $POSTGRES_USER $POSTGRES_DB > backups/backup_$timestamp.sql
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