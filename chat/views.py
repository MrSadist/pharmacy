from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from user.models import CustomUser
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Chat.objects.none()

        user = self.request.user
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return Chat.objects.none()

        queryset = Chat.objects.filter(Q(user=user) | Q(specialist=user)).select_related('user', 'specialist')

        specialist_id = self.request.query_params.get('specialist_id')
        if specialist_id:
            try:
                specialist_id = int(specialist_id)
                queryset = Chat.objects.filter(specialist__id=specialist_id).select_related('user', 'specialist')
            except ValueError:
                raise serializers.ValidationError({'specialist_id': 'Invalid specialist ID'})

        return queryset

    @swagger_auto_schema(
        operation_summary="Получить список чатов",
        operation_description="Возвращает список чатов текущего пользователя (как user или specialist). Поддерживается фильтр по specialist_id для получения чатов, где указанный специалист участвует.",
        responses={
            200: ChatSerializer(many=True),
            401: "Неаутентифицированный пользователь",
            400: "Неверный формат specialist_id"
        },
        manual_parameters=[
            openapi.Parameter('specialist_id', openapi.IN_QUERY, description="Фильтр по ID специалиста", type=openapi.TYPE_INTEGER),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные чата",
        operation_description="Возвращает данные конкретного чата по его ID.",
        responses={
            200: ChatSerializer(),
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к чату",
            404: "Чат не найден"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать чат",
        operation_description="Создаёт новый чат между текущим пользователем и специалистом. Возвращает полные данные специалиста.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["specialist_id"],
            properties={
                "specialist_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID специалиста")
            },
            example={"specialist_id": 1}
        ),
        responses={
            201: ChatSerializer(),
            200: ChatSerializer(),
            400: "Специалист не найден или чат уже существует",
            403: "Только пользователи могут создавать чаты",
            401: "Неаутентифицированный пользователь"
        }
    )
    def create(self, request, *args, **kwargs):
        specialist_id = request.data.get('specialist_id')
        try:
            specialist = CustomUser.objects.get(id=specialist_id, role='specialist')
        except CustomUser.DoesNotExist:
            logger.error(f"Specialist with ID {specialist_id} not found")
            return Response({'error': 'Specialist not found'}, status=status.HTTP_400_BAD_REQUEST)

        existing_chat = Chat.objects.filter(user=request.user, specialist=specialist).first()
        if existing_chat:
            logger.info(f"Chat already exists: user {request.user.id}, specialist {specialist.id}")
            serializer = self.get_serializer(existing_chat)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"Chat created: user {request.user.id}, specialist {specialist.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        specialist_id = self.request.data.get('specialist_id')
        try:
            specialist = CustomUser.objects.get(id=specialist_id, role='specialist')
        except CustomUser.DoesNotExist:
            logger.error(f"Specialist with ID {specialist_id} not found")
            raise serializers.ValidationError({'specialist_id': 'Specialist not found'})

        serializer.save(user=self.request.user, specialist=specialist)

    @swagger_auto_schema(
        operation_summary="Создать чат по ID пользователя и специалиста",
        operation_description="Создаёт чат между указанным пользователем и специалистом (или возвращает существующий). Доступно только для администраторов или специалистов (для своих чатов). Возвращает полные данные чата, включая пользователя и специалиста.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_id", "specialist_id"],
            properties={
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                "specialist_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID специалиста")
            },
            example={"user_id": 2, "specialist_id": 1}
        ),
        responses={
            201: ChatSerializer(),
            200: ChatSerializer(),
            400: "Пользователь или специалист не найден",
            401: "Неаутентифицированный пользователь",
            403: "Нет прав для создания чата"
        }
    )
    @action(detail=False, methods=['post'])
    def create_by_ids(self, request):
        user_id = request.data.get('user_id')
        specialist_id = request.data.get('specialist_id')

        if not request.user.is_authenticated:
            logger.error("Unauthenticated user attempted to create chat")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not (request.user.is_staff or request.user.role == 'specialist'):
            logger.warning(f"User {request.user.id} attempted to create chat without admin or specialist privileges")
            return Response({'error': 'Only admins or specialists can create chats by IDs'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.role == 'specialist' and request.user.id != specialist_id:
            logger.warning(f"Specialist {request.user.id} attempted to create chat for another specialist {specialist_id}")
            return Response({'error': 'Specialists can only create chats for themselves'}, status=status.HTTP_403_FORBIDDEN)

        if not user_id or not specialist_id:
            logger.error("Missing user_id or specialist_id in request")
            return Response({'error': 'Both user_id and specialist_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id, role='user')
        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} not found or not a user")
            return Response({'error': 'User not found or not a user'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            specialist = CustomUser.objects.get(id=specialist_id, role='specialist')
        except CustomUser.DoesNotExist:
            logger.error(f"Specialist with ID {specialist_id} not found or not a specialist")
            return Response({'error': 'Specialist not found or not a specialist'}, status=status.HTTP_400_BAD_REQUEST)

        existing_chat = Chat.objects.filter(user=user, specialist=specialist).first()
        if existing_chat:
            logger.info(f"Chat already exists: user {user_id}, specialist {specialist_id}")
            serializer = self.get_serializer(existing_chat)
            return Response(serializer.data, status=status.HTTP_200_OK)

        try:
            chat = Chat.objects.create(user=user, specialist=specialist)
            serializer = self.get_serializer(chat)
            logger.info(f"Chat created: user {user_id}, specialist {specialist_id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating chat: {str(e)}")
            return Response({'error': 'Failed to create chat'}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Обновить данные чата",
        operation_description="Обновляет данные указанного чата по его ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "specialist_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID нового специалиста")
            },
            example={"specialist_id": 2}
        ),
        responses={
            200: ChatSerializer(),
            400: "Специалист не найден",
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к чату",
            404: "Чат не найден"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные чата",
        operation_description="Частично обновляет данные указанного чата по его ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "specialist_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID нового специалиста")
            },
            example={"specialist_id": 3}
        ),
        responses={
            200: ChatSerializer(),
            400: "Специалист не найден",
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к чату",
            404: "Чат не найден"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить чат",
        operation_description="Удаляет чат по его ID. Доступно только участникам чата.",
        responses={
            204: "Нет содержимого",
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к чату",
            404: "Чат не найден"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить сообщения чата",
        operation_description="Возвращает список всех сообщений в указанном чате.",
        responses={
            200: MessageSerializer(many=True),
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к чату",
            404: "Чат не найден"
        }
    )
    @action(detail=True, methods=['get'], serializer_class=MessageSerializer)
    def messages(self, request, pk=None):
        chat = self.get_object()
        messages = chat.messages.all()
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()

        user = self.request.user
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return Message.objects.none()

        chats = Chat.objects.filter(Q(user=user) | Q(specialist=user))
        return Message.objects.filter(chat__in=chats).select_related('chat', 'sender')

    @swagger_auto_schema(
        operation_summary="Получить список сообщений",
        operation_description="Возвращает список сообщений в чатах, где текущий пользователь является участником.",
        responses={
            200: MessageSerializer(many=True),
            401: "Неаутентифицированный пользователь"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные сообщения",
        operation_description="Возвращает данные конкретного сообщения по его ID.",
        responses={
            200: MessageSerializer(),
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к сообщению",
            404: "Сообщение не найдено"
        }
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
            example={"chat": 1, "text": "Привет, как дела?"}
        ),
        responses={
            201: MessageSerializer(),
            400: "Чат не найден",
            403: "Вы не участник этого чата",
            401: "Неаутентифицированный пользователь"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        chat_id = self.request.data.get('chat')
        try:
            chat = Chat.objects.get(id=chat_id)
            if self.request.user not in [chat.user, chat.specialist]:
                logger.warning(f"User {self.request.user.id} attempted to send message to chat {chat_id} without permission")
                return Response({'error': 'You are not a participant of this chat'}, status=status.HTTP_403_FORBIDDEN)
        except Chat.DoesNotExist:
            logger.error(f"Chat with ID {chat_id} not found")
            return Response({'error': 'Chat not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(chat=chat, sender=self.request.user)
        logger.info(f"Message sent by user {self.request.user.id} in chat {chat_id}")

    @swagger_auto_schema(
        operation_summary="Обновить сообщение",
        operation_description="Обновляет текст указанного сообщения по его ID. Доступно только отправителю.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "text": openapi.Schema(type=openapi.TYPE_STRING, description="Обновлённый текст сообщения")
            },
            example={"text": "Привет, всё отлично!"}
        ),
        responses={
            200: MessageSerializer(),
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к сообщению",
            404: "Сообщение не найдено"
        }
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
            example={"text": "Привет, всё супер!"}
        ),
        responses={
            200: MessageSerializer(),
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к сообщению",
            404: "Сообщение не найдено"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить сообщение",
        operation_description="Удаляет сообщение по его ID. Доступно только отправителю.",
        responses={
            204: "Нет содержимого",
            401: "Неаутентифицированный пользователь",
            403: "Нет доступа к сообщению",
            404: "Сообщение не найдено"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)