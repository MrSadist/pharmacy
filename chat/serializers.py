# chat/serializers.py
from rest_framework import serializers
from .models import Chat, Message
from user.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'surname', 'role']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialist = UserSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'user', 'specialist', 'created_at', 'messages']