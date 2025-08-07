from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
import requests
import json
import time
import uuid
from datetime import datetime

from .models import (
    QualityChatSession, 
    QualityChatMessage, 
    QualityChatResponse,
    QualityKnowledgeBase,
    QualityChatAnalytics
)
from .serializers import (
    QualityChatSessionSerializer,
    QualityChatMessageSerializer,
    QualityChatResponseSerializer,
    QualityKnowledgeBaseSerializer,
    QualityChatAnalyticsSerializer,
    ChatMessageCreateSerializer,
    ChatResponseSerializer,
    ChatSessionCreateSerializer,
    ChatHistorySerializer
)


# Configuration
N8N_WEBHOOK_URL = "https://meiyume.app.n8n.cloud/webhook/9c73c27e-0fd2-470f-9064-5d3e55ee08ef/chat"


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_sessions_list(request):
    """List all chat sessions for the authenticated user"""
    sessions = QualityChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-updated_at')
    
    serializer = QualityChatSessionSerializer(sessions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chat_session(request):
    """Create a new chat session"""
    serializer = ChatSessionCreateSerializer(data=request.data)
    if serializer.is_valid():
        session_id = serializer.validated_data.get('session_id') or f"session_{int(time.time())}"
        title = serializer.validated_data.get('title', 'New Quality Chat Session')
        
        session = QualityChatSession.objects.create(
            user=request.user,
            session_id=session_id,
            title=title
        )
        
        response_serializer = QualityChatSessionSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_session_detail(request, session_id):
    """Get details of a specific chat session"""
    session = get_object_or_404(
        QualityChatSession,
        session_id=session_id,
        user=request.user
    )
    
    serializer = QualityChatSessionSerializer(session)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_chat_session(request, session_id):
    """Delete a chat session"""
    session = get_object_or_404(
        QualityChatSession,
        session_id=session_id,
        user=request.user
    )
    
    session.is_active = False
    session.save()
    
    return Response({'message': 'Session deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_messages_list(request, session_id):
    """Get all messages for a chat session"""
    session = get_object_or_404(
        QualityChatSession,
        session_id=session_id,
        user=request.user
    )
    
    messages = session.messages.all().order_by('timestamp')
    serializer = QualityChatMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_chat_message(request):
    """Send a message to the Quality RAG Chat and get AI response"""
    serializer = ChatMessageCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    message_content = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id', f"session_{int(time.time())}")
    metadata = serializer.validated_data.get('metadata', {})
    
    # Get or create chat session
    session, created = QualityChatSession.objects.get_or_create(
        session_id=session_id,
        user=request.user,
        defaults={'title': 'Quality Chat Session'}
    )
    
    # Create user message
    user_message = QualityChatMessage.objects.create(
        session=session,
        message_type='user',
        content=message_content,
        metadata=metadata
    )
    
    # Send to n8n webhook
    start_time = time.time()
    try:
        payload = {
            "chatInput": message_content,  # Standardized field name for n8n
            "sessionId": session_id,  # Standardized field name for n8n
            "message": message_content,  # Keep for backward compatibility
            "chat_id": session_id,  # Keep for backward compatibility
            "user_id": request.user.username,
            "timestamp": datetime.now().isoformat(),
            "session_data": {
                "chat_history": list(session.messages.values('content', 'message_type', 'timestamp')[-5:]),
                "user_preferences": {
                    "username": request.user.username,
                    "email": request.user.email
                }
            }
        }
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            try:
                result = response.json()
                ai_response = result.get("response", "I apologize, but I couldn't generate a response at this time.")
                response_metadata = result.get("metadata", {})
                
                # Create assistant message
                assistant_message = QualityChatMessage.objects.create(
                    session=session,
                    message_type='assistant',
                    content=ai_response,
                    metadata=response_metadata,
                    response_time=processing_time,
                    tokens_used=result.get("tokens_used"),
                    model_used=result.get("model_used", "n8n-ai")
                )
                
                # Create response record
                QualityChatResponse.objects.create(
                    message=assistant_message,
                    status='success',
                    n8n_webhook_url=N8N_WEBHOOK_URL,
                    n8n_response=result,
                    processing_time=processing_time
                )
                
                # Update session
                session.updated_at = timezone.now()
                session.save()
                
                return Response({
                    'message': ai_response,
                    'metadata': response_metadata,
                    'session_id': session_id,
                    'processing_time': processing_time
                })
                
            except json.JSONDecodeError:
                # Handle plain text response
                ai_response = response.text
                
                assistant_message = QualityChatMessage.objects.create(
                    session=session,
                    message_type='assistant',
                    content=ai_response,
                    response_time=processing_time,
                    model_used="n8n-ai"
                )
                
                QualityChatResponse.objects.create(
                    message=assistant_message,
                    status='success',
                    n8n_webhook_url=N8N_WEBHOOK_URL,
                    n8n_response={'raw_response': ai_response},
                    processing_time=processing_time
                )
                
                session.updated_at = timezone.now()
                session.save()
                
                return Response({
                    'message': ai_response,
                    'session_id': session_id,
                    'processing_time': processing_time
                })
        else:
            # Handle error response
            error_message = f"Error: Unable to get response (Status: {response.status_code})"
            
            assistant_message = QualityChatMessage.objects.create(
                session=session,
                message_type='assistant',
                content=error_message,
                response_time=processing_time
            )
            
            QualityChatResponse.objects.create(
                message=assistant_message,
                status='error',
                n8n_webhook_url=N8N_WEBHOOK_URL,
                error_message=f"HTTP {response.status_code}: {response.text}",
                processing_time=processing_time
            )
            
            return Response({
                'error': error_message,
                'session_id': session_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except requests.exceptions.RequestException as e:
        error_message = f"Connection error: {str(e)}"
        
        assistant_message = QualityChatMessage.objects.create(
            session=session,
            message_type='assistant',
            content=error_message,
            response_time=time.time() - start_time
        )
        
        QualityChatResponse.objects.create(
            message=assistant_message,
            status='error',
            n8n_webhook_url=N8N_WEBHOOK_URL,
            error_message=str(e),
            processing_time=time.time() - start_time
        )
        
        return Response({
            'error': error_message,
            'session_id': session_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, session_id):
    """Get complete chat history with analytics"""
    session = get_object_or_404(
        QualityChatSession,
        session_id=session_id,
        user=request.user
    )
    
    messages = session.messages.all().order_by('timestamp')
    analytics = getattr(session, 'analytics', None)
    
    data = {
        'session_id': session_id,
        'messages': QualityChatMessageSerializer(messages, many=True).data,
        'analytics': QualityChatAnalyticsSerializer(analytics).data if analytics else None
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge_base_search(request):
    """Search the quality knowledge base"""
    query = request.GET.get('q', '')
    entry_type = request.GET.get('type', '')
    
    queryset = QualityKnowledgeBase.objects.filter(is_active=True)
    
    if query:
        queryset = queryset.filter(
            models.Q(title__icontains=query) |
            models.Q(content__icontains=query) |
            models.Q(tags__contains=[query])
        )
    
    if entry_type:
        queryset = queryset.filter(entry_type=entry_type)
    
    serializer = QualityKnowledgeBaseSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_analytics(request, session_id):
    """Get analytics for a chat session"""
    session = get_object_or_404(
        QualityChatSession,
        session_id=session_id,
        user=request.user
    )
    
    analytics, created = QualityChatAnalytics.objects.get_or_create(
        session=session,
        defaults={
            'total_messages': session.messages.count(),
            'user_messages': session.messages.filter(message_type='user').count(),
            'assistant_messages': session.messages.filter(message_type='assistant').count(),
            'total_tokens_used': sum(
                msg.tokens_used or 0 for msg in session.messages.filter(message_type='assistant')
            ),
            'average_response_time': session.messages.filter(
                message_type='assistant', response_time__isnull=False
            ).aggregate(avg_time=models.Avg('response_time'))['avg_time'],
            'session_duration': (session.updated_at - session.created_at).total_seconds()
        }
    )
    
    if not created:
        # Update analytics
        analytics.total_messages = session.messages.count()
        analytics.user_messages = session.messages.filter(message_type='user').count()
        analytics.assistant_messages = session.messages.filter(message_type='assistant').count()
        analytics.total_tokens_used = sum(
            msg.tokens_used or 0 for msg in session.messages.filter(message_type='assistant')
        )
        analytics.average_response_time = session.messages.filter(
            message_type='assistant', response_time__isnull=False
        ).aggregate(avg_time=models.Avg('response_time'))['avg_time']
        analytics.session_duration = (session.updated_at - session.created_at).total_seconds()
        analytics.save()
    
    serializer = QualityChatAnalyticsSerializer(analytics)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """Check system status including n8n webhook"""
    try:
        response = requests.get(N8N_WEBHOOK_URL.replace("/chat", "/health"), timeout=5)
        n8n_status = "online" if response.status_code == 200 else "issues"
    except:
        n8n_status = "offline"
    
    return Response({
        'n8n_webhook_status': n8n_status,
        'webhook_url': N8N_WEBHOOK_URL,
        'timestamp': timezone.now().isoformat()
    }) 