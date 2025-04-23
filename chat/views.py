from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from .permissions import ChatPermission
from user.models import CustomUser
from django.db.models import Q

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [ChatPermission]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(Q(user=user) | Q(specialist=user))

    @swagger_auto_schema(
        operation_summary="Получить список чатов",
        operation_description="Возвращает список чатов текущего пользователя (как user или specialist) с информацией о пользователе, специалисте и дате создания.",
        responses={200: ChatSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные чата",
        operation_description="Возвращает данные конкретного чата по его ID, включая информацию о пользователе, специалисте и сообщения.",
        responses={200: ChatSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать чат",
        operation_description="Создаёт новый чат между пользователем и специалистом.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["specialist"],
            properties={
                "specialist": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID специалиста")
            },
            example={
                "specialist": 1
            }
        ),
        responses={
            201: ChatSerializer(),
            400: "Специалист не найден"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        specialist_id = self.request.data.get('specialist')
        try:
            specialist = CustomUser.objects.get(id=specialist_id, role='specialist')
        except CustomUser.DoesNotExist:
            return Response({'error': 'Specialist not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(user=self.request.user, specialist=specialist)

    @swagger_auto_schema(
        operation_summary="Обновить данные чата (полное обновление)",
        operation_description="Обновляет данные указанного чата по его ID, например, специалиста.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "specialist": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID нового специалиста")
            },
            example={
                "specialist": 2
            }
        ),
        responses={
            200: ChatSerializer(),
            400: "Специалист не найден"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные чата",
        operation_description="Частично обновляет данные указанного чата по его ID, например, специалиста.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "specialist": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID нового специалиста")
            },
            example={
                "specialist": 3
            }
        ),
        responses={
            200: ChatSerializer(),
            400: "Специалист не найден"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить чат",
        operation_description="Удаляет чат по его ID. Доступно только участникам чата.",
        responses={204: "Нет содержимого"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [ChatPermission]

    def get_queryset(self):
        user = self.request.user
        chats = Chat.objects.filter(Q(user=user) | Q(specialist=user))
        return Message.objects.filter(chat__in=chats)

    @swagger_auto_schema(
        operation_summary="Получить список сообщений",
        operation_description="Возвращает список сообщений в чатах, где текущий пользователь является участником (user или specialist).",
        responses={200: MessageSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные сообщения",
        operation_description="Возвращает данные конкретного сообщения по его ID, включая информацию о чате и отправителе.",
        responses={200: MessageSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Отправить сообщение",
        operation_description="Отправляет новое сообщение в указанный чат.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["chat", "text"],
            properties={
                "chat": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID чата"),
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Текст сообщения")
            },
            example={
                "chat": 1,
                "text": "Привет, как дела?"
            }
        ),
        responses={
            201: MessageSerializer(),
            400: "Чат не найден"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        chat_id = self.request.data.get('chat')
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(chat=chat, sender=self.request.user)

    @swagger_auto_schema(
        operation_summary="Обновить сообщение (полное обновление)",
        operation_description="Обновляет текст указанного сообщения по его ID. Доступно только отправителю.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Обновлённый текст сообщения")
            },
            example={
                "text": "Привет, всё отлично!"
            }
        ),
        responses={200: MessageSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить сообщение",
        operation_description="Частично обновляет текст указанного сообщения по его ID. Доступно только отправителю.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Обновлённый текст сообщения")
            },
            example={
                "text": "Привет, всё супер!"
            }
        ),
        responses={200: MessageSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить сообщение",
        operation_description="Удаляет сообщение по его ID. Доступно только отправителю.",
        responses={204: "Нет содержимого"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)