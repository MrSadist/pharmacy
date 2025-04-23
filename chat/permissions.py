from rest_framework import permissions

class ChatPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Для GET (просмотр чатов и сообщений) — доступно всем аутентифицированным
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для создания чата (POST в ChatViewSet)
        if view.basename == 'chat' and request.method == 'POST':
            # Только пользователи (role='user') могут начать чат
            return request.user.role == 'user'

        # Для отправки сообщений (POST в MessageViewSet)
        if view.basename == 'message' and request.method == 'POST':
            chat_id = request.data.get('chat')
            try:
                chat = Chat.objects.get(id=chat_id)
                # Только участники чата могут отправлять сообщения
                return request.user in [chat.user, chat.specialist]
            except Chat.DoesNotExist:
                return False

        return True

    def has_object_permission(self, request, view, obj):
        # Для редактирования/удаления сообщений (PUT, DELETE в MessageViewSet)
        if view.basename == 'message' and request.method in ['PUT', 'DELETE']:
            # Только отправитель сообщения может его редактировать/удалять
            return obj.sender == request.user

        return True