#!/bin/bash

# Production Environment Setup Script
echo "🏭 Setting up Production Environment..."

# Create production environment file
if [ ! -f .env.prod ]; then
    echo "📋 Creating .env.prod from template..."
    cp env_template.txt .env.prod
fi

echo "📝 Please update .env.prod with these production settings:"
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
echo "✏️  Edit .env.prod manually, then run: ./scripts/prod-start.sh" 