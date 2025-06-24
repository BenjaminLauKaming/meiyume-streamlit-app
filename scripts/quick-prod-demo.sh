#!/bin/bash

# Quick Production Demo Script
echo "🏭 Setting up Production Demo Environment..."

# Create production config with minimal changes for demo
echo "📝 Creating production configuration..."

# Copy current env and modify for production
cp .env .env.prod

# Update critical production settings in .env.prod
echo "🔧 Updating production settings..."

# For demo purposes, we'll modify just the critical settings
# In real production, you'd set these manually

# Create temporary .env for production
cat > .env << EOF
# Production Environment Configuration (Demo)

# Environment
ENVIRONMENT=production
DEBUG=False
DJANGO_SETTINGS_MODULE=ai_cad_analyzer.settings.production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Security (Demo - use stronger in real production)
SECRET_KEY=$(python3 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")

# Database Configuration (Production)
DATABASE_URL=postgresql://cad_user:cad_password_prod@db:5432/cad_analyzer_prod
POSTGRES_DB=cad_analyzer_prod
POSTGRES_USER=cad_user
POSTGRES_PASSWORD=cad_password_prod

# Redis Configuration
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=redis_password

# Celery Configuration
CELERY_BROKER_URL=redis://:redis_password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:redis_password@redis:6379/0

# n8n Configuration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/cad-analysis
N8N_WEBHOOK_SECRET=prod-webhook-secret
N8N_FORM_URL=http://localhost:5678/form/ffc0c29a-e891-4521-b822-e0d1ac468a19
N8N_ADMIN_USER=admin
N8N_ADMIN_PASSWORD=admin123
N8N_HOST=localhost:5678

# Google AI Configuration
GOOGLE_GEMINI_API_KEY=${GOOGLE_GEMINI_API_KEY:-your-gemini-api-key-here}

# Azure AD Configuration (Demo)
AZURE_AD_CLIENT_ID=demo-client-id
AZURE_AD_CLIENT_SECRET=demo-client-secret
AZURE_AD_TENANT_ID=demo-tenant-id

# CORS Configuration (Production)
CORS_ALLOWED_ORIGINS=https://localhost:443,http://localhost:80,http://127.0.0.1:80

# Email Configuration (Console for demo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# File Storage (Local for demo - use S3 in real production)
AWS_ACCESS_KEY_ID=demo-aws-key
AWS_SECRET_ACCESS_KEY=demo-aws-secret
AWS_STORAGE_BUCKET_NAME=demo-bucket
AWS_S3_REGION_NAME=us-east-1

# Additional Runtime Configuration
DJANGO_API_URL=http://django:8000
SITE_DOMAIN=https://localhost
STREAMLIT_SERVER_PORT=8501
DJANGO_SERVER_PORT=8000
N8N_SERVER_PORT=5678
EOF

echo "✅ Production configuration created!"
echo "🚀 Starting production environment..."

# Start production environment
docker-compose -f docker-compose.prod.yml up --build -d

echo "⏳ Waiting for services to start..."
sleep 20

echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate

echo "📦 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput

echo "👤 Creating superuser..."
docker-compose -f docker-compose.prod.yml exec django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Production superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo ""
echo "🎉 Production Environment Ready!"
echo ""
echo "🌐 Access your production app at:"
echo "   • Main App: http://localhost (via Nginx)"
echo "   • Django Admin: http://localhost/admin"
echo "   • n8n Workflows: http://localhost/n8n"
echo ""
echo "📊 Monitor with:"
echo "   • docker-compose -f docker-compose.prod.yml logs -f"
echo "   • docker-compose -f docker-compose.prod.yml ps"
echo ""
echo "🛑 Stop with: docker-compose -f docker-compose.prod.yml down" 