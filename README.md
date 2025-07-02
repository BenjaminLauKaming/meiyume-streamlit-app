# Meiyume AI Assistant

A comprehensive full-stack application for multiple AI-powered assistants. The system currently supports CAD analysis and is designed to easily accommodate additional AI assistants through a modular architecture.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     Django      │    │      n8n        │
│   Frontend      │◄──►│    Backend      │◄──►│   Workflows     │
│                 │    │   REST API      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              │                         │
                       ┌─────────────┐         ┌─────────────┐
                       │ PostgreSQL  │         │   Multiple  │
                       │  Database   │         │   AI Models │
                       └─────────────┘         └─────────────┘
```

## Current AI Assistants

### 1. CAD Analysis Assistant
- Analyzes 2D CAD PDF drawings using Google Gemini AI
- Extracts dimensions, tolerances, and part relationships
- Generates structured CSV reports and analysis documents

### 2. Quality Assistant (Coming Soon)
- Quality control and inspection analysis
- Defect detection and classification
- Quality metrics and reporting

### 3. Complaint Assistant (Coming Soon)
- Customer complaint analysis and categorization
- Sentiment analysis and priority assessment
- Automated response suggestions

## Project Structure

```
meiyume_ai_assistant/
├── streamlit_app/         # Streamlit UI code
│   ├── main.py           # Main application entry point
│   ├── cadAssistant.py   # CAD analysis interface
│   ├── qualityAssistant.py # Quality analysis interface
│   ├── complaintAssistant.py # Complaint analysis interface
│   └── auth_utils.py     # Authentication utilities
├── backend/               # Django project
│   ├── manage.py
│   ├── meiyume_core/     # Core Django app for shared functionality
│   │   ├── models.py     # Base models and shared functionality
│   │   ├── views.py      # Shared API views
│   │   ├── serializers.py # Shared serializers
│   │   ├── urls.py       # Core URL patterns
│   │   ├── admin.py      # Admin interface
│   │   └── utils.py      # Shared utilities
│   ├── assistants/       # Individual assistant modules
│   │   ├── cad/          # CAD analysis assistant
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   └── workflows.py
│   │   ├── quality/      # Quality assistant (future)
│   │   └── complaint/    # Complaint assistant (future)
│   └── meiyume_ai_assistant/ # Django settings, urls, etc.
│       ├── settings.py
│       ├── urls.py
│       └── wsgi.py
├── n8n/                   # n8n workflow configurations
│   ├── cad_analysis_workflow.json
│   ├── quality_analysis_workflow.json (future)
│   └── complaint_analysis_workflow.json (future)
├── requirements.txt       # Python dependencies
├── env_template.txt       # Environment variables template
└── README.md             # This file
```

## Features

### Core Platform Features
- **Modular Architecture**: Easy to add new AI assistants
- **Unified Authentication**: Azure AD integration with SSO
- **Multi-Assistant Support**: Switch between different AI assistants
- **Real-time Processing**: Live status updates via webhooks
- **Results Export**: CSV and report downloads for all assistants
- **Admin Interface**: Django admin for system management

### CAD Analysis Features
- **File Upload**: Secure PDF upload with validation
- **AI Analysis**: Google Gemini-powered extraction of:
  - Dimensions and measurements
  - Tolerance specifications
  - Part relationships and assembly info
  - Material specifications
- **Engineering Reports**: Detailed analysis with visualizations

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+ (for n8n)
- Redis (for Celery, optional)
- PostgreSQL (for production)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd meiyume_ai_assistant

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

# Stop n8n and import workflows
# Import cad_analysis_workflow.json for CAD analysis
```

### 5. Start Development Environment

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or start services individually
cd backend && python manage.py runserver
cd streamlit_app && streamlit run main.py
```

## Access Points

- **Main Application**: http://localhost:8501
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/
- **n8n Workflows**: http://localhost:5678

## Adding New AI Assistants

The platform is designed to easily accommodate new AI assistants:

1. **Create Assistant Module**: Add new directory under `backend/assistants/`
2. **Define Models**: Create models for the assistant's data
3. **Create Views**: Implement API endpoints
4. **Add n8n Workflow**: Create workflow for the assistant
5. **Update Frontend**: Add interface in Streamlit app
6. **Configure URLs**: Add routing for the new assistant

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is proprietary software. All rights reserved. 