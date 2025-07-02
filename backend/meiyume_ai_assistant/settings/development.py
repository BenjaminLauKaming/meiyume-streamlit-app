"""
Development settings for meiyume_ai_assistant project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '0.0.0.0', 'django']

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# CORS Settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Development database (SQLite by default)
if not config('DATABASE_URL', default=None):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Django REST Framework for development
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Add browsable API for dev
    ],
})

# Logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cad_core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache (dummy cache for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Development-specific settings
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Disable some security in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0 

# Use n8n Cloud URLs (or environment variables if set)
N8N_WEBHOOK_URL = config('N8N_WEBHOOK_URL', default='https://meiyume.app.n8n.cloud/webhook/fe198a5f-79e0-4dc7-82d1-ce7fb65e9c5e')
N8N_FORM_URL = config('N8N_FORM_URL', default='https://meiyume.app.n8n.cloud/form/cb9d8f80-4e72-4abb-acdf-80abad36abe2')