from rest_framework import serializers
from .models import (
    QualityChatSession, 
    QualityChatMessage, 
    QualityChatResponse,
    QualityKnowledgeBase,
    QualityChatAnalytics
)


class QualityChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for Quality Chat Sessions"""
    
    message_count = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    
    class Meta:
        model = QualityChatSession
        fields = [
            'id', 'session_id', 'title', 'created_at', 'updated_at', 
            'is_active', 'message_count', 'last_message_time'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message_time(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        return last_message.timestamp if last_message else None


class QualityChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for Quality Chat Messages"""
    
    class Meta:
        model = QualityChatMessage
        fields = [
            'id', 'session', 'message_type', 'content', 'metadata',
            'timestamp', 'response_time', 'tokens_used', 'model_used'
        ]
        read_only_fields = ['id', 'timestamp']


class QualityChatResponseSerializer(serializers.ModelSerializer):
    """Serializer for Quality Chat Responses"""
    
    class Meta:
        model = QualityChatResponse
        fields = [
            'id', 'message', 'status', 'n8n_webhook_url', 'n8n_response',
            'processing_time', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class QualityKnowledgeBaseSerializer(serializers.ModelSerializer):
    """Serializer for Quality Knowledge Base"""
    
    class Meta:
        model = QualityKnowledgeBase
        fields = [
            'id', 'title', 'content', 'entry_type', 'tags', 'source',
            'version', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QualityChatAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for Quality Chat Analytics"""
    
    class Meta:
        model = QualityChatAnalytics
        fields = [
            'id', 'session', 'total_messages', 'user_messages', 'assistant_messages',
            'total_tokens_used', 'average_response_time', 'topics_discussed',
            'session_duration', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatMessageCreateSerializer(serializers.Serializer):
    """Serializer for creating new chat messages"""
    
    message = serializers.CharField(max_length=5000)
    session_id = serializers.CharField(max_length=255, required=False)
    metadata = serializers.JSONField(required=False, default=dict)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses from n8n"""
    
    response = serializers.CharField()
    metadata = serializers.JSONField(required=False, default=dict)
    session_id = serializers.CharField()
    message_id = serializers.CharField()
    processing_time = serializers.FloatField(required=False)
    tokens_used = serializers.IntegerField(required=False)
    model_used = serializers.CharField(required=False)


class ChatSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating new chat sessions"""
    
    title = serializers.CharField(max_length=500, required=False)
    session_id = serializers.CharField(max_length=255, required=False)


class ChatHistorySerializer(serializers.Serializer):
    """Serializer for chat history"""
    
    session_id = serializers.CharField()
    messages = QualityChatMessageSerializer(many=True)
    analytics = QualityChatAnalyticsSerializer(required=False) 