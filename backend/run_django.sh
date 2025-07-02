#!/bin/bash

# Helper script to run Django commands with the correct settings module
export DJANGO_SETTINGS_MODULE=meiyume_ai_assistant.settings.development

# Run the Django command
python manage.py "$@" 