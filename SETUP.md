# CAD Analyzer - Development & Production Setup Guide

This guide covers setting up both development and production environments using Docker, PostgreSQL, and modern DevOps practices.

## 📋 Prerequisites

- Docker Desktop (4.0+)
- Docker Compose (2.0+)
- Git
- Python 3.11+ (for local development)

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Production"
        A[Nginx] --> B[Streamlit Frontend]
        A --> C[Django API]
        A --> D[n8n Workflows]
        C --> E[PostgreSQL]
        C --> F[Redis]
        G[Celery Workers] --> F
    end
    
    subgraph "Development"
        H[Streamlit] --> I[Django API]
        I --> J[PostgreSQL]
        I --> K[Redis]
        L[n8n] --> I
    end
```

## 🚀 Quick Start

### Development Environment

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd Meiyume_project
   cp env_template.txt .env
   ```

2. **Configure Environment**
   Edit `.env` file with your settings:
   ```bash
   # Minimum required settings
   GOOGLE_GEMINI_API_KEY=your-real-api-key-here
   SECRET_KEY=your-secret-key-here
   ```

3. **Start Development Environment**
   ```bash
   ./scripts/dev-start.sh
   ```

4. **Access Services**
   - 🌐 **Frontend**: http://localhost:8501
   - 🔧 **Django Admin**: http://localhost:8000/admin (admin/admin123)
   - 📊 **n8n Workflows**: http://localhost:5678 (admin/admin123)

### Production Environment

1. **Configure Production Environment**
   ```bash
   cp env_template.txt .env
   # Edit .env with production settings
   ```

2. **Start Production Environment**
   ```bash
   ./scripts/prod-start.sh
   ```

3. **Access Services**
   - 🌐 **Main App**: https://localhost
   - 🔧 **Admin**: https://localhost/admin
   - 📊 **n8n**: https://localhost/n8n

## 📁 Project Structure

```
Meiyume_project/
├── backend/                     # Django backend
│   ├── ai_cad_analyzer/        # Project settings
│   │   ├── settings/           # Environment-specific settings
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── cad_core/               # Main application
├── streamlit_app/              # Frontend application
├── docker/                     # Docker configurations
│   ├── django/                 # Django containers
│   ├── streamlit/              # Streamlit containers
│   ├── nginx/                  # Nginx proxy
│   └── postgres/               # Database init
├── scripts/                    # Deployment scripts
├── n8n/                        # n8n workflows
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
└── env_template.txt            # Environment template
```

## 🗄️ Database Management

### **No Liquibase Required!**

Django has its own excellent migration system. You don't need Liquibase for this project.

### Database Operations

**Create Migration:**
```bash
# Development
docker-compose exec django python manage.py makemigrations

# Production
docker-compose -f docker-compose.prod.yml exec django python manage.py makemigrations
```

**Apply Migrations:**
```bash
# Development
docker-compose exec django python manage.py migrate

# Production
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate
```

**Database Shell:**
```bash
# Development
docker-compose exec db psql -U cad_user -d cad_analyzer_dev

# Production
docker-compose -f docker-compose.prod.yml exec db psql -U cad_user -d cad_analyzer_prod
```

## 🔧 Environment Configuration

### Development Settings (`.env`)

```bash
# Environment
ENVIRONMENT=development
DEBUG=True
DJANGO_SETTINGS_MODULE=ai_cad_analyzer.settings.development

# Database
DATABASE_URL=postgresql://cad_user:cad_password@localhost:5432/cad_analyzer_dev

# AI
GOOGLE_GEMINI_API_KEY=your-real-api-key-here

# n8n
N8N_FORM_URL=http://localhost:5678/form/ffc0c29a-e891-4521-b822-e0d1ac468a19
```

### Production Settings (`.env`)

```bash
# Environment
ENVIRONMENT=production
DEBUG=False
DJANGO_SETTINGS_MODULE=ai_cad_analyzer.settings.production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Security
SECRET_KEY=your-secret-key-here
SECURE_SSL_REDIRECT=True

# Database
DATABASE_URL=postgresql://cad_user:strong_password@db:5432/cad_analyzer_prod

# File Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-s3-bucket

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

## 🔄 CI/CD Pipeline Suggestions

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Add your deployment commands here
          ./scripts/prod-start.sh
```

## 📊 Monitoring & Logging

### Development Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f django
docker-compose logs -f streamlit
docker-compose logs -f n8n

# Monitor resources
docker-compose top
```

### Production Monitoring

```bash
# Service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Resource monitoring
docker stats
```

## 🛡️ Security Considerations

### Development
- ✅ Default credentials for quick setup
- ✅ CORS allows all origins
- ✅ Debug mode enabled
- ✅ Console email backend

### Production
- 🔒 Strong passwords required
- 🔒 SSL/TLS encryption
- 🔒 Restricted CORS origins
- 🔒 Security headers enabled
- 🔒 Non-root containers
- 🔒 AWS S3 for file storage
- 🔒 Sentry error tracking

## 📦 Deployment Options

### Option 1: Single Server Docker Deployment
- Use the provided production scripts
- Suitable for small to medium applications
- Easy to maintain and scale vertically

### Option 2: Kubernetes Deployment
```bash
# Convert to Kubernetes manifests
kompose convert -f docker-compose.prod.yml
```

### Option 3: Cloud Platform Deployment
- **AWS**: ECS, EKS, or Elastic Beanstalk
- **Google Cloud**: Cloud Run or GKE
- **Azure**: Container Instances or AKS

## 🔧 Common Operations

### Backup Database
```bash
# Create backup
docker exec cad_analyzer_db_prod pg_dump -U cad_user cad_analyzer_prod > backup.sql

# Restore backup
docker exec -i cad_analyzer_db_prod psql -U cad_user cad_analyzer_prod < backup.sql
```

### Update Application
```bash
# Development
docker-compose down
git pull
docker-compose up --build -d

# Production
./scripts/prod-start.sh  # Handles backup and update
```

### Scale Services
```bash
# Scale celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery=3
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Issues:**
```bash
# Check database logs
docker-compose logs db

# Test connection
docker-compose exec django python manage.py dbshell
```

**Port Conflicts:**
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8501
lsof -i :5432
```

**Permission Issues:**
```bash
# Fix permissions
sudo chown -R $USER:$USER .
```

### Health Checks

```bash
# Quick health check
curl http://localhost/health

# Detailed service check
docker-compose ps
docker-compose top
```

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs -f`
2. Review environment configuration
3. Ensure all required environment variables are set
4. Check Docker and Docker Compose versions

---

## 🎯 Key Benefits of This Setup

✅ **No Liquibase needed** - Django migrations handle database changes  
✅ **Environment separation** - Different configs for dev/prod  
✅ **Scalable architecture** - Easy to scale individual services  
✅ **Security-first** - Production-ready security configurations  
✅ **Monitoring ready** - Comprehensive logging and health checks  
✅ **DevOps friendly** - Easy CI/CD integration  
✅ **PostgreSQL optimized** - Proper database configuration and backups 