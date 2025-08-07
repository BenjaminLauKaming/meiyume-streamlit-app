"""
URL patterns for Quality assistant including RAG Chat functionality
"""

from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    # Chat session management
    path('chat/sessions/', views.chat_sessions_list, name='chat_sessions_list'),
    path('chat/sessions/create/', views.create_chat_session, name='create_chat_session'),
    path('chat/sessions/<str:session_id>/', views.chat_session_detail, name='chat_session_detail'),
    path('chat/sessions/<str:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
    
    # Chat messages
    path('chat/sessions/<str:session_id>/messages/', views.chat_messages_list, name='chat_messages_list'),
    path('chat/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/sessions/<str:session_id>/history/', views.chat_history, name='chat_history'),
    
    # Analytics and knowledge base
    path('chat/sessions/<str:session_id>/analytics/', views.chat_analytics, name='chat_analytics'),
    path('chat/knowledge-base/search/', views.knowledge_base_search, name='knowledge_base_search'),
    
    # System status
    path('chat/system-status/', views.system_status, name='system_status'),
] 