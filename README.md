# AI CAD Analyzer

A full-stack application for analyzing 2D CAD PDF drawings using AI. The system extracts dimensions, tolerances, and part relationships from engineering drawings using Google Gemini AI, orchestrated through an n8n workflow.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     Django      │    │      n8n        │
│   Frontend      │◄──►│    Backend      │◄──►│   Workflow      │
│                 │    │   REST API      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              │                         │
                       ┌─────────────┐         ┌─────────────┐
                       │ PostgreSQL  │         │   Google    │
                       │  Database   │         │   Gemini    │
                       └─────────────┘         └─────────────┘
```

## Project Structure

```
ai-cad-analyzer/
├── streamlit_app/         # Streamlit UI code
│   └── main.py
├── backend/               # Django project
│   ├── manage.py
│   ├── cad_core/          # Django app for uploads, models, API
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── utils.py
│   └── ai_cad_analyzer/   # Django settings, urls, etc.
│       ├── settings.py
│       ├── urls.py
│       └── wsgi.py
├── n8n/                   # n8n workflow JSON export, docs
│   └── cad_analysis_workflow.json
├── requirements.txt       # Python dependencies
├── env_template.txt       # Environment variables template
└── README.md             # This file
```

## Features

- **File Upload**: Secure PDF upload with validation
- **AI Analysis**: Google Gemini-powered extraction of:
  - Dimensions and measurements
  - Tolerance specifications
  - Part relationships and assembly info
  - Material specifications
- **Real-time Processing**: Live status updates via webhooks
- **Results Export**: CSV and report downloads
- **User Management**: Azure AD integration with SSO
- **Admin Interface**: Django admin for system management

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+ (for n8n)
- Redis (for Celery, optional)
- PostgreSQL (for production)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd ai-cad-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the environment template and configure:

```bash
cp env_template.txt .env
```

Edit `.env` with your configuration:

```env
# Required
SECRET_KEY=your-django-secret-key
GOOGLE_GEMINI_API_KEY=your-gemini-api-key
N8N_WEBHOOK_SECRET=your-webhook-secret

# Optional (for Azure AD)
AZURE_AD_CLIENT_ID=your-azure-ad-client-id
AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
AZURE_AD_TENANT_ID=your-azure-ad-tenant-id
```

### 3. Database Setup

```bash
cd backend

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. n8n Setup

Install and configure n8n:

```bash
# Install n8n globally
npm install -g n8n

# Start n8n (first time - creates config)
n8n start

# Stop n8n and import workflow
# Go to http://localhost:5678
# Import the workflow from n8n/cad_analysis_workflow.json
```

Configure n8n:
1. Set up Google Gemini credentials
2. Set webhook secret environment variable
3. Activate the workflow

### 5. Running the Application

Start all services:

```bash
# Terminal 1: Django Backend
cd backend
python manage.py runserver

# Terminal 2: Streamlit Frontend  
streamlit run streamlit_app/main.py

# Terminal 3: n8n (if not running as service)
n8n start
```

Access the application:
- **Streamlit UI**: http://localhost:8501
- **Django API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **n8n Interface**: http://localhost:5678

## API Endpoints

### File Upload
```
POST /api/uploads/
Content-Type: multipart/form-data

{
  "file": <PDF file>,
  "metadata": "{\"project_name\": \"Example Project\"}",
  "analysis_options": {
    "extract_dimensions": true,
    "extract_tolerances": true,
    "analyze_part_relationships": true
  }
}
```

### Check Processing Status
```
GET /api/results/{task_id}/

Response:
{
  "task_id": "uuid",
  "status": "completed|processing|failed",
  "progress": 100,
  "results": {
    "dimensions": [...],
    "tolerances": [...],
    "relationships": [...]
  },
  "download_urls": {
    "dimensions_csv": "url",
    "tolerances_csv": "url"
  }
}
```

### Dashboard Stats
```
GET /api/dashboard/stats/

Response:
{
  "total_uploads": 25,
  "completed_uploads": 20,
  "failed_uploads": 2,
  "processing_uploads": 3,
  "recent_uploads": [...]
}
```

## Data Flow

1. **Upload**: User uploads PDF via Streamlit
2. **Storage**: Django saves file and creates database record
3. **Webhook**: Django sends file URL and metadata to n8n
4. **Processing**: n8n downloads PDF, extracts text, sends to Gemini
5. **Analysis**: Gemini analyzes content and returns structured data
6. **Callback**: n8n sends results back to Django webhook
7. **Storage**: Django stores results and generates CSV files
8. **Display**: Streamlit polls for status and displays results

## Security Features

- **Authentication**: Token-based auth with Azure AD integration
- **File Validation**: PDF-only uploads with size limits
- **Webhook Security**: Secret-based validation for n8n callbacks
- **CORS Protection**: Configured for specific origins
- **Input Sanitization**: All inputs validated and sanitized

## Production Deployment

### Environment Variables for Production

```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=cad_analyzer_db
DB_USER=db_user
DB_PASSWORD=secure_password
DB_HOST=db_host
SITE_DOMAIN=https://your-domain.com
```

### Database Migration

```bash
# PostgreSQL setup
pip install psycopg2-binary
python manage.py migrate

# Collect static files
python manage.py collectstatic
```

### Docker Deployment (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  django:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dbname
    depends_on:
      - db
      - redis

  streamlit:
    build: .
    command: streamlit run streamlit_app/main.py
    ports:
      - "8501:8501"
    depends_on:
      - django

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: cad_analyzer
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password

  redis:
    image: redis:6
    
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
```

## Troubleshooting

### Common Issues

1. **n8n Webhook Not Responding**
   - Check n8n is running on port 5678
   - Verify webhook URL in Django settings
   - Check webhook secret matches

2. **File Upload Fails**
   - Verify file is PDF format
   - Check file size (10MB limit)
   - Ensure Django media directory exists

3. **Gemini API Errors**
   - Verify API key is correct
   - Check rate limits
   - Ensure n8n has Gemini credentials configured

4. **Database Connection Issues**
   - Check database credentials
   - Verify PostgreSQL is running
   - Run migrations if needed

### Logs

Check application logs:

```bash
# Django logs
tail -f backend/logs/django.log

# n8n logs
# Available in n8n interface under executions

# Streamlit logs
# Visible in terminal running streamlit
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

[Add your license information here]

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section 