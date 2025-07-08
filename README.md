# Meiyume AI Assistant

A comprehensive full-stack application for multiple AI-powered assistants. The system currently supports CAD analysis and is designed to easily accommodate additional AI assistants through a modular architecture with JWT authentication and Azure AD integration.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     Django      │    │      n8n        │
│   Frontend      │◄──►│    Backend      │◄──►│   Workflows     │
│   (Port 8501)   │    │   REST API      │    │   (Port 5678)   │
│                 │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌────────┴────────┐              │
         │              │                 │              │
         │         ┌─────────────┐  ┌─────────────┐      │
         │         │ PostgreSQL  │  │   Redis     │      │
         │         │  Database   │  │   (Port     │      │
         │         │ (Port 5433) │  │   6379)     │      │
         │         └─────────────┘  └─────────────┘      │
         │                                              │
         │         ┌─────────────┐         ┌─────────────┐
         └────────►│   JWT       │         │   Multiple  │
                   │   Auth      │         │   AI Models │
                   │   Tokens    │         │ (Gemini,    │
                   └─────────────┘         │  OpenAI)    │
                                           └─────────────┘
```

## 🔐 Authentication & Security

### JWT Authentication
- **Access Token Lifetime**: 24 hours
- **Refresh Token Lifetime**: 7 days
- **Token Rotation**: Enabled
- **Token Blacklisting**: Enabled
- **Algorithm**: HS256

### Azure AD Integration
- **SSO**: Single Sign-On with Microsoft credentials
- **OAuth2**: Standard OAuth2 flow
- **Enterprise**: Company-wide authentication

### API Security
- **CORS**: Configured for specific origins
- **CSRF Protection**: Enabled
- **Rate Limiting**: Configurable
- **File Upload Validation**: PDF files only, 10MB limit

## 🚀 Quick Start Commands

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd Meiyume_project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env_template.txt .env
# Edit .env with your configuration

# Database setup
cd backend
./run_django.sh makemigrations
./run_django.sh migrate
./run_django.sh createsuperuser

# Start services
docker-compose up -d
```

### Useful Django Commands
```bash
cd backend

# Use the helper script (recommended)
./run_django.sh check              # Check Django configuration
./run_django.sh makemigrations     # Create migrations
./run_django.sh migrate            # Apply migrations
./run_django.sh runserver          # Start development server
./run_django.sh createsuperuser    # Create admin user
./run_django.sh collectstatic      # Collect static files
./run_django.sh shell              # Django shell

# Or set environment manually
export DJANGO_SETTINGS_MODULE=meiyume_ai_assistant.settings.development
python manage.py [command]
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f django
docker-compose logs -f streamlit
docker-compose logs -f n8n

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Database Commands
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U cad_user -d meiyume_ai_assistant_dev

# Backup database
docker-compose exec db pg_dump -U cad_user meiyume_ai_assistant_dev > backup.sql

# Restore database
docker-compose exec -T db psql -U cad_user -d meiyume_ai_assistant_dev < backup.sql
```

## 📁 Project Structure

```
Meiyume_project/
├── backend/                     # Django backend
│   ├── manage.py               # Django management script
│   ├── run_django.sh           # Helper script for Django commands
│   ├── meiyume_core/           # Core shared functionality
│   │   ├── models.py           # Base models (BaseUpload, UserPreferences, etc.)
│   │   ├── views.py            # Shared views (Dashboard, Health, Preferences)
│   │   ├── serializers.py      # Shared serializers
│   │   ├── urls.py             # Core URL patterns
│   │   ├── admin.py            # Core admin interface
│   │   └── migrations/         # Core migrations
│   ├── assistants/             # Individual assistant modules
│   │   ├── cad/                # CAD Analysis Assistant
│   │   │   ├── models.py       # CADUpload, CADAnalysisOptions, CADAnalysisResult
│   │   │   ├── views.py        # CAD-specific views and webhooks
│   │   │   ├── serializers.py  # CAD-specific serializers
│   │   │   ├── urls.py         # CAD API routes
│   │   │   ├── admin.py        # CAD admin interface
│   │   │   ├── utils.py        # CAD utilities (n8n integration)
│   │   │   └── migrations/     # CAD migrations
│   │   ├── quality/            # Quality Assistant (placeholder)
│   │   └── complaint/          # Complaint Assistant (placeholder)
│   └── meiyume_ai_assistant/   # Django project settings
│       ├── settings/           # Environment-specific settings
│       │   ├── base.py         # Base settings
│       │   ├── development.py  # Development settings
│       │   └── production.py   # Production settings
│       ├── urls.py             # Main URL configuration
│       ├── wsgi.py             # WSGI configuration
│       └── asgi.py             # ASGI configuration
├── frontend/                   # Streamlit frontend
│   ├── main.py                # Multi-assistant interface
│   ├── engAssistant.py        # CAD Analysis Assistant
│   ├── qualityAssistant.py    # Quality Assistant (placeholder)
│   ├── complaintAssistant.py  # Complaint Assistant (placeholder)
│   └── auth_utils.py          # Authentication utilities
├── n8n/                       # n8n workflow configurations
│   └── cad_analysis_workflow_backup.json
├── docker/                    # Docker configurations
│   ├── django/               # Django Dockerfiles
│   ├── nginx/                # Nginx configuration
│   ├── postgres/             # PostgreSQL setup
│   └── streamlit/            # Streamlit Dockerfiles
├── scripts/                   # Utility scripts
│   ├── dev-start.sh          # Development startup
│   ├── prod-start.sh         # Production startup
│   └── setup-production.sh   # Production setup
├── docker-compose.yml         # Development Docker Compose
├── docker-compose.prod.yml    # Production Docker Compose
├── requirements.txt           # Python dependencies
├── env_template.txt           # Environment variables template
└── README.md                 # This file
```

## 🔌 API Endpoints

### Authentication Endpoints
```
POST   /api/token/           # Obtain JWT token
POST   /api/token/refresh/   # Refresh JWT token
POST   /api/token/verify/    # Verify JWT token
```

### Core Endpoints
```
GET    /api/                 # API root with documentation
GET    /api/preferences/     # User preferences
PUT    /api/preferences/     # Update user preferences
GET    /api/dashboard/stats/ # Dashboard statistics
GET    /api/health/          # Health check
GET    /api/logs/            # Processing logs
```

### CAD Assistant Endpoints
```
POST   /api/cad/uploads/           # Upload CAD file
GET    /api/cad/uploads/           # List CAD uploads
GET    /api/cad/uploads/<id>/      # Get upload details
DELETE /api/cad/uploads/<id>/      # Delete upload
GET    /api/cad/results/           # List analysis results
GET    /api/cad/results/<id>/      # Get specific results
GET    /api/cad/options/<id>/      # Get analysis options
PUT    /api/cad/options/<id>/      # Update analysis options
POST   /api/cad/webhook/n8n-callback/ # n8n webhook callback
```

### Quality Assistant Endpoints (Future)
```
POST   /api/quality/uploads/       # Upload quality data
GET    /api/quality/results/       # Get quality analysis
```

### Complaint Assistant Endpoints (Future)
```
POST   /api/complaint/analyze/     # Analyze complaint
GET    /api/complaint/history/     # Get complaint history
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
SECRET_KEY=your-django-secret-key
GOOGLE_GEMINI_API_KEY=your-gemini-api-key
N8N_WEBHOOK_SECRET=your-webhook-secret

# Database
DATABASE_URL=postgresql://cad_user:cad_password@localhost:5433/meiyume_ai_assistant_dev
DB_ENGINE=django.db.backends.postgresql
DB_NAME=meiyume_ai_assistant_dev
DB_USER=cad_user
DB_PASSWORD=cad_password
DB_HOST=localhost
DB_PORT=5433

# Azure AD (Optional)
AZURE_AD_CLIENT_ID=your-azure-ad-client-id
AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_AD_TENANT_ID=your-azure-ad-tenant-id

# n8n Configuration
N8N_WEBHOOK_URL=https://meiyume.app.n8n.cloud/webhook/fe198a5f-79e0-4dc7-82d1-ce7fb65e9c5e
N8N_FORM_URL=https://meiyume.app.n8n.cloud/form/cb9d8f80-4e72-4abb-acdf-80abad36abe2

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### JWT Configuration
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

## 🎯 Current AI Assistants

### 1. CAD Analysis Assistant ✅
- **Purpose**: Analyze 2D CAD PDF drawings
- **AI Model**: Google Gemini 2.5 Flash
- **Features**:
  - Dimension extraction and validation
  - Tolerance analysis
  - Part relationship mapping
  - Material specification detection
  - Assembly component identification
  - CSV report generation
  - Engineering visualization

### 2. Quality Assistant 🚧 (Coming Soon)
- **Purpose**: Quality control and inspection analysis
- **Features**:
  - Defect detection and classification
  - Quality metrics calculation
  - Compliance checking
  - Statistical process control
  - Automated reporting

### 3. Complaint Assistant 🚧 (Coming Soon)
- **Purpose**: Customer complaint analysis
- **Features**:
  - Sentiment analysis
  - Priority assessment
  - Root cause analysis
  - Automated response suggestions
  - Trend analysis

## 🔄 Data Flow

### CAD Analysis Flow
1. **Upload**: User uploads PDF via Streamlit
2. **Validation**: Django validates file and creates record
3. **Processing**: Django sends to n8n webhook
4. **AI Analysis**: n8n calls Google Gemini API
5. **Results**: n8n sends structured data back to Django
6. **Storage**: Django stores results and generates files
7. **Display**: Streamlit shows results to user

### Authentication Flow
1. **Login**: User authenticates via Azure AD or JWT
2. **Token**: System issues JWT access and refresh tokens
3. **API Calls**: Frontend includes Bearer token in requests
4. **Validation**: Django validates token for each request
5. **Refresh**: Tokens automatically refreshed when needed

## 🛠️ Development Workflow

### Adding New Assistant
1. **Create Module**: `backend/assistants/new_assistant/`
2. **Define Models**: Inherit from base models
3. **Create Views**: Implement API endpoints
4. **Add Serializers**: Handle data serialization
5. **Configure URLs**: Add routing
6. **Create n8n Workflow**: Design AI processing
7. **Add Frontend**: Create Streamlit interface
8. **Update Admin**: Configure admin interface
9. **Test**: Verify functionality
10. **Deploy**: Apply to production

### Database Migrations
```bash
# Create migrations for new models
./run_django.sh makemigrations assistants.new_assistant

# Apply migrations
./run_django.sh migrate

# Check migration status
./run_django.sh showmigrations
```

## 🚀 Deployment

### Development
```bash
# Start development environment
./scripts/dev-start.sh

# Access points
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
# Admin: http://localhost:8000/admin
# n8n: http://localhost:5678
```

### Production
```bash
# Setup production environment
./scripts/setup-production.sh

# Start production services
./scripts/prod-start.sh

# Access points
# Main App: https://your-domain.com
# Admin: https://your-domain.com/admin
# n8n: https://your-domain.com/n8n
```

## 🔍 Monitoring & Debugging

### Logs
```bash
# Django logs
docker-compose logs -f django

# Streamlit logs
docker-compose logs -f streamlit

# n8n logs
docker-compose logs -f n8n

# Database logs
docker-compose logs -f db
```

### Health Checks
```bash
# API health
curl http://localhost:8000/api/health/

# Database connection
./run_django.sh dbshell

# Redis connection
docker-compose exec redis redis-cli ping
```

### Common Issues
- **Database Connection**: Check PostgreSQL is running and credentials are correct
- **JWT Issues**: Verify token expiration and signing key
- **File Uploads**: Check file size limits and media directory permissions
- **n8n Integration**: Verify webhook URLs and secrets

## 📚 API Documentation

### Authentication
All API endpoints require authentication via JWT Bearer token:
```bash
curl -H "Authorization: Bearer <your-jwt-token>" \
     http://localhost:8000/api/cad/uploads/
```

### File Upload Example
```bash
curl -X POST \
  -H "Authorization: Bearer <your-jwt-token>" \
  -F "file=@drawing.pdf" \
  -F "project_name=Project Alpha" \
  -F "drawing_number=DWG-001" \
  http://localhost:8000/api/cad/uploads/
```

### Get Results Example
```bash
curl -H "Authorization: Bearer <your-jwt-token>" \
     http://localhost:8000/api/cad/results/<upload-id>/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Contact the development team 