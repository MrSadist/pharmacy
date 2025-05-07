from rest_framework import serializers
from user.models import CustomUser
from .models import Chat, Message
from user.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    chat = serializers.PrimaryKeyRelatedField(queryset=Chat.objects.all())

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'created_at', 'is_read']
        read_only_fields = ['id', 'sender', 'created_at', 'is_read']

    def validate(self, data):
        chat = data.get('chat')
        user = self.context['request'].user
        if user not in [chat.user, chat.specialist]:
            raise serializers.ValidationError("You are not a participant of this chat.")
        return data

class ChatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialist = UserSerializer(read_only=True)
    specialist_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='specialist'),
        source='specialist',
        write_only=True
    )
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'user', 'specialist', 'specialist_id', 'created_at', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'messages', 'specialist']

    def validate(self, data):
        user = self.context['request'].user
        specialist = data.get('specialist')
        if Chat.objects.filter(user=user, specialist=specialist).exists():
            raise serializers.ValidationError({'detail': 'Chat between this user and specialist already exists'})
        return data

    def get_messages(self, obj):
        if self.context['request'].query_params.get('include_messages', 'false') == 'true':
            return MessageSerializer(obj.messages.all(), many=True).data
        return []