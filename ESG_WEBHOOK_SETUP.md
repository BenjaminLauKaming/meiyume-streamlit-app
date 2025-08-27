# ESG Assistant Webhook Setup Guide

## Overview

This guide explains how to set up the ESG Assistant with n8n workflow integration using Django backend webhooks to receive analysis results.

## Architecture

```
Streamlit Frontend → n8n Workflow → Django Webhook → Database → Frontend (polling/results)
```

## Setup Steps

### 1. Django Backend Setup

#### Install Dependencies
```bash
cd backend
pip install djangorestframework djangorestframework-simplejwt python-decouple dj-database-url
```

#### Database Setup
Create a `.env` file in the backend directory:
```bash
# Database Configuration
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-ngrok-url.ngrok.io

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-here
```

#### Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

#### Start Django Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### 2. Ngrok Setup (for local development)

#### Install Ngrok
```bash
# Download from https://ngrok.com/download
# Or install via package manager:
brew install ngrok  # macOS
```

#### Expose Django Server
```bash
ngrok http 8000
```

This will give you a public URL like: `https://abc123.ngrok.io`

### 3. n8n Workflow Configuration

#### Webhook URL Configuration
In your n8n workflow, add a webhook node that sends results to:
```
https://your-ngrok-url.ngrok.io/api/esg/webhook/
```

#### Required Payload Format
The n8n workflow should send a POST request with this JSON structure:
```json
{
  "execution_id": "n8n-execution-id",
  "upload_id": "uuid-from-frontend",
  "document_language": "English",
  "total_volume_litres": 1500.5,
  "currency": "USD",
  "total_cost": 250.75,
  "billing_period": "January 2024",
  "confidence_score": 0.95,
  "status": "success",
  "raw_analysis": {
    "full_analysis_data": "..."
  }
}
```

#### Error Handling
For errors, send:
```json
{
  "execution_id": "n8n-execution-id",
  "upload_id": "uuid-from-frontend",
  "status": "error",
  "error_message": "Analysis failed: reason"
}
```

### 4. Frontend Integration (Future Enhancement)

To fully integrate with the Django backend, update the ESG assistant:

```python
# In esgAssistant.py, replace the analyze_esg_document function:

def analyze_esg_document(uploaded_file):
    # Step 1: Create upload record in Django
    backend_url = "http://localhost:8000"  # or your ngrok URL
    
    upload_data = {
        'filename': uploaded_file.name,
        'file_size': uploaded_file.size,
        'document_type': 'other',
    }
    
    # Get JWT token
    headers = {}
    if 'jwt_tokens' in st.session_state:
        headers['Authorization'] = f"Bearer {st.session_state.jwt_tokens['access']}"
    
    # Create upload record
    response = requests.post(f"{backend_url}/api/esg/create-upload/", 
                           json=upload_data, headers=headers)
    
    if response.status_code == 201:
        upload_info = response.json()
        upload_id = upload_info['upload_id']
        
        # Step 2: Submit to n8n with upload_id
        files = {'pdfFile': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {
            'upload_id': upload_id,
            'webhook_url': f"{backend_url}/api/esg/webhook/"
        }
        
        n8n_response = requests.post(
            "https://meiyume.app.n8n.cloud/form/6592d141-79ea-4923-809b-152a546662f7",
            files=files, 
            data=data
        )
        
        # Step 3: Poll for results
        if n8n_response.status_code == 200:
            poll_for_results(upload_id, backend_url, headers)
```

## API Endpoints

### ESG Upload Endpoints
- `GET /api/esg/uploads/` - List user's ESG uploads
- `POST /api/esg/create-upload/` - Create upload record
- `GET /api/esg/uploads/{id}/status/` - Check upload status
- `GET /api/esg/results/{upload_id}/` - Get analysis results

### Webhook Endpoint
- `POST /api/esg/webhook/` - Receive n8n results (no auth required)

### Dashboard
- `GET /api/esg/dashboard/stats/` - Get ESG statistics

## Testing

### Test Webhook Locally
```bash
curl -X POST http://localhost:8000/api/esg/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "test-uuid",
    "document_language": "English",
    "total_volume_litres": 1500.5,
    "status": "success"
  }'
```

### Test with Ngrok
```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/esg/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "test-uuid",
    "document_language": "English", 
    "total_volume_litres": 1500.5,
    "status": "success"
  }'
```

## Troubleshooting

### Common Issues

1. **Database not configured**: Update `.env` file with correct database settings
2. **Migrations not applied**: Run `python manage.py migrate`
3. **Ngrok URL changes**: Update n8n workflow webhook URL when ngrok restarts
4. **CORS issues**: Add your ngrok URL to `ALLOWED_HOSTS` in settings
5. **Authentication errors**: Ensure JWT tokens are properly configured

### Debug Mode
Enable Django debug logging:
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'assistants.esg': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Production Deployment

For production:
1. Use a proper database (PostgreSQL)
2. Set up proper domain instead of ngrok
3. Configure SSL certificates
4. Set `DEBUG=False`
5. Use environment variables for sensitive data
6. Set up proper logging and monitoring

## Next Steps

1. Complete Django backend setup and migrations
2. Set up ngrok tunnel
3. Configure n8n workflow to send webhook
4. Test the complete flow
5. Update frontend to use backend integration
6. Deploy to production environment
