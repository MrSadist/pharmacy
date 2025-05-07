from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, RegisterSerializer, UserProfileSerializer, LoginSerializer, OTPSerializer, \
 ExtendedUserSerializer, AdminUserUpdateSerializer
from products.models import Product
from products.serializers import ProductSerializers
from django.core.mail import send_mail
from django.conf import settings
import random
from datetime import timedelta
from .models import CustomUser
from django.utils import timezone
from rest_framework import serializers
from .permissions import IsAdminUser


class AdminUserListAPI(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = CustomUser.objects.all()
        role = self.request.query_params.get('role')
        email = self.request.query_params.get('email')
        is_active = self.request.query_params.get('is_active')

        if role:
            queryset = queryset.filter(role=role)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    @swagger_auto_schema(
        operation_summary="Получить список всех пользователей",
        operation_description="Возвращает список всех пользователей для администратора. Поддерживает фильтрацию по роли, email и статусу активности.",
        manual_parameters=[
            openapi.Parameter(
                'role', openapi.IN_QUERY,
                description="Фильтр по роли пользователя (user или specialist)",
                type=openapi.TYPE_STRING, enum=['user', 'specialist']
            ),
            openapi.Parameter(
                'email', openapi.IN_QUERY,
                description="Фильтр по email (частичное совпадение)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_active', openapi.IN_QUERY,
                description="Фильтр по статусу активности (true/false)",
                type=openapi.TYPE_BOOLEAN
            ),
        ],
        responses={
            200: openapi.Response(
                description="Список пользователей",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                            "email": openapi.Schema(type=openapi.TYPE_STRING, format="email",
                                                    description="Электронная почта"),
                            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                            "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                            "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                            "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара"),
                            "role": openapi.Schema(type=openapi.TYPE_STRING, description="Роль пользователя")
                        }
                    )
                )
            ),
            403: "Доступ запрещён"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminUserCreateAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Создать нового пользователя",
        operation_description="Создаёт нового пользователя от имени администратора. Отправляет OTP для пользователей с ролью 'user'.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "name", "surname", "phone_number", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri",
                                         description="URL аватара (опционально)"),
                "role": openapi.Schema(type=openapi.TYPE_STRING, enum=['user', "specialist"], description="Роль (по умолчанию 'user')")
            },
            example={
                "email": "newuser@example.com",
                "name": "Алексей",
                "surname": "Смирнов",
                "phone_number": "+998901234567",
                "password": "securepassword123",
                "avatar": "https://example.com/avatar.jpg",
                "role": "user"
            }
        ),
        responses={
            201: openapi.Response(
                description="Пользователь создан",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email",
                                                        description="Электронная почта"),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri",
                                                         description="URL аватара"),
                                "role": openapi.Schema(type=openapi.TYPE_STRING, description="Роль")
                            }
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об успехе")
                    }
                )
            ),
            403: "Доступ запрещён",
            400: "Неверные данные"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        class ExtendedUserSerializer(UserSerializer):
            role = serializers.CharField(read_only=True)

            class Meta(UserSerializer.Meta):
                fields = ['id', 'email', 'name', 'surname', 'phone_number', 'avatar', 'role']

        if user.role == 'user':
            otp = str(random.randint(100000, 999999))
            user.otp_code = otp
            user.otp_created_at = timezone.now()
            user.save()

            send_mail(
                'Your Verification Code',
                f'Your OTP code is: {otp}. The code is valid for 5 minutes.',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return Response({
                'user': ExtendedUserSerializer(user).data,
                'message': 'User created. OTP sent to email.'
            }, status=201)

        return Response({
            'user': ExtendedUserSerializer(user).data,
            'message': 'User created.'
        }, status=201)


class AdminUserDetailAPI(generics.RetrieveUpdateAPIView):
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAdminUser]
    queryset = CustomUser.objects.all()
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary="Получить данные пользователя",
        operation_description="Возвращает данные пользователя по ID для администратора.",
        responses={
            200: openapi.Response(
                description="Данные пользователя",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email",
                                                description="Электронная почта"),
                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                        "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                        "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара"),
                        "role": openapi.Schema(type=openapi.TYPE_STRING, description="Роль пользователя"),
                        "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Активен ли пользователь"),
                        "is_staff": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                   description="Является ли пользователь персоналом"),
                        "is_superuser": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                       description="Является ли пользователь суперпользователем")
                    }
                )
            ),
            403: "Доступ запрещён",
            404: "Пользователь не найден"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить данные пользователя",
        operation_description="Обновляет данные пользователя по ID (полное или частичное). Доступно только для администраторов.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара"),
                "role": openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'specialist'], description="Роль"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Новый пароль (опционально)"),
                "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Активен ли пользователь"),
                "is_staff": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                           description="Является ли пользователь персоналом"),
                "is_superuser": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                               description="Является ли пользователь суперпользователем")
            },
            example={
                "email": "updated@example.com",
                "name": "Игорь",
                "surname": "Петров",
                "phone_number": "+998901234567",
                "avatar": "https://example.com/new_avatar.jpg",
                "role": "specialist",
                "password": "newpassword123",
                "is_active": True,
                "is_staff": True,
                "is_superuser": False
            }
        ),
        responses={
            200: openapi.Response(
                description="Пользователь обновлён",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email",
                                                description="Электронная почта"),
                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                        "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                        "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара"),
                        "role": openapi.Schema(type=openapi.TYPE_STRING, description="Роль пользователя"),
                        "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Активен ли пользователь"),
                        "is_staff": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                   description="Является ли пользователь персоналом"),
                        "is_superuser": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                       description="Является ли пользователь суперпользователем")
                    }
                )
            ),
            403: "Доступ запрещён",
            404: "Пользователь не найден",
            400: "Неверные данные"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные пользователя",
        operation_description="Частично обновляет данные пользователя по ID. Доступно только для администраторов.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара"),
                "role": openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'specialist'], description="Роль"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Новый пароль (опционально)"),
                "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Активен ли пользователь"),
                "is_staff": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                           description="Является ли пользователь персоналом"),
                "is_superuser": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                               description="Является ли пользователь суперпользователем")
            },
            example={
                "name": "Игорь",
                "role": "specialist",
                "is_active": True
            }
        ),
        responses={
            200: openapi.Response(
                description="Пользователь обновлён",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email",
                                                description="Электронная почта"),
                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                        "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                        "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара"),
                        "role": openapi.Schema(type=openapi.TYPE_STRING, description="Роль пользователя"),
                        "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Активен ли пользователь"),
                        "is_staff": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                   description="Является ли пользователь персоналом"),
                        "is_superuser": openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                                       description="Является ли пользователь суперпользователем")
                    }
                )
            ),
            403: "Доступ запрещён",
            404: "Пользователь не найден",
            400: "Неверные данные"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class AdminUserDeleteAPI(generics.DestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = CustomUser.objects.all()
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary="Удалить пользователя",
        operation_description="Удаляет пользователя по ID. Доступно только для администраторов.",
        responses={
            204: openapi.Response(description="Пользователь удалён"),
            403: "Доступ запрещён",
            404: "Пользователь не найден"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        operation_description="Создаёт нового пользователя с указанным email, именем, фамилией, номером телефона, паролем и ролью (опционально). Если роль 'specialist', пользователь получает доступ к админке и токены без OTP. Для роли 'user' отправляется OTP-код на email для верификации.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "name", "surname", "phone_number", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя (например, +998901234567)"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль пользователя"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя (опционально)"),
                "role": openapi.Schema(type=openapi.TYPE_STRING, enum=['user', 'specialist'], description="Роль пользователя (опционально, по умолчанию 'user')")
            },
            example={
                "email": "user@example.com",
                "name": "Иван",
                "surname": "Иванов",
                "phone_number": "+998901234567",
                "password": "securepassword123",
                "avatar": "https://example.com/avatar.jpg",
                "role": "specialist"
            }
        ),
        responses={
            201: openapi.Response(
                description="Пользователь успешно создан",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя"),
                                "role": openapi.Schema(type=openapi.TYPE_STRING, description="Роль пользователя")
                            }
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об успехе"),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh-токен (только для specialist)"),
                        "access": openapi.Schema(type=openapi.TYPE_STRING, description="Access-токен (только для specialist)")
                    },
                    example={
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "name": "Иван",
                            "surname": "Иванов",
                            "phone_number": "+998901234567",
                            "avatar": "https://example.com/avatar.jpg",
                            "role": "specialist"
                        },
                        "message": "User created. Tokens generated for specialist.",
                        "refresh": "refresh_token_example",
                        "access": "access_token_example"
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Если роль specialist, выдаем токены без OTP
        if user.role == 'specialist':
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': ExtendedUserSerializer(user).data,
                'message': 'User created. Tokens generated for specialist.',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=201)

        # Для роли user отправляем OTP
        otp = str(random.randint(100000, 999999))
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save()

        send_mail(
            'Your Verification Code',
            f'Your OTP code is: {otp}. The code is valid for 5 minutes.',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        return Response({
            'user': ExtendedUserSerializer(user).data,
            'message': 'User created. OTP sent to email.'
        }, status=201)

class SpecialistListAPI(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  # Можно изменить на AllowAny, если список публичный

    def get_queryset(self):
        return CustomUser.objects.filter(role='specialist')

    @swagger_auto_schema(
        operation_summary="Получить список специалистов",
        operation_description="Возвращает список всех пользователей с ролью 'specialist'. Доступно только для аутентифицированных пользователей.",
        responses={
            200: openapi.Response(
                description="Список специалистов",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                            "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта"),
                            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                            "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                            "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона"),
                            "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара")
                        }
                    )
                )
            ),
            401: "Неавторизован"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class LoginAPI(APIView):
    @swagger_auto_schema(
        operation_summary="Вход пользователя",
        operation_description="Аутентифицирует пользователя по email и паролю, после чего отправляет OTP-код на email для верификации.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль пользователя"),
            },
            example={
                "email": "user@example.com",
                "password": "securepassword123",
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP-код отправлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об успехе")
                    },
                    example={
                        "message": "OTP sent to your email"
                    }
                )
            ),
            401: "Неверные учетные данные"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(email=email, password=password)

        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)

        if user.role == 'specialist':
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful. Tokens generated for specialist.',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=200)

        otp = str(random.randint(100000, 999999))
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save()

        send_mail(
            'Your Verification Code',
            f'Your OTP code is: {otp}. The code is valid for 5 minutes.',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return Response({'message': 'OTP sent to your email'})

class VerifyOTPAPI(APIView):
    @swagger_auto_schema(
        operation_summary="Верификация OTP-кода",
        operation_description="Проверяет OTP-код, отправленный на email пользователя, и возвращает токены доступа, если код верный и не истёк.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "otp_code"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                "otp_code": openapi.Schema(type=openapi.TYPE_STRING, description="OTP-код, отправленный на email")
            },
            example={
                "email": "user@example.com",
                "otp_code": "123456"
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешная верификация",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя")
                            }
                        ),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh-токен"),
                        "access": openapi.Schema(type=openapi.TYPE_STRING, description="Access-токен")
                    },
                    example={
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "name": "Иван",
                            "surname": "Иванов",
                            "phone_number": "+998901234567",
                            "avatar": "https://example.com/avatar.jpg"
                        },
                        "refresh": "refresh_token_example",
                        "access": "access_token_example"
                    }
                )
            ),
            400: "Неверный или истёкший OTP-код",
            404: "Пользователь не найден"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']

        try:
            user = CustomUser.objects.get(email=email)
            if (user.otp_code != otp_code or
                    timezone.now() - user.otp_created_at > timedelta(minutes=5)):
                return Response({'error': 'Invalid or expired OTP'}, status=400)

            user.otp_code = None
            user.otp_created_at = None
            user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class UserProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_summary="Получить профиль пользователя",
        operation_description="Возвращает данные профиля текущего аутентифицированного пользователя, включая email, имя, фамилию, номер телефона, аватар и избранные продукты.",
        responses={
            200: openapi.Response(
                description="Профиль пользователя",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                        "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                        "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя"),
                        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль (зашифрованный, не возвращается)"),
                        "favorites": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Описание продукта"),
                                    "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена продукта")
                                }
                            ),
                            description="Список избранных продуктов"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить профиль пользователя (полное обновление)",
        operation_description="Обновляет данные профиля текущего аутентифицированного пользователя.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Новый пароль пользователя")
            },
            example={
                "email": "updated_user@example.com",
                "name": "Пётр",
                "surname": "Петров",
                "phone_number": "+998901234567",
                "avatar": "https://example.com/avatar.jpg",
                "password": "newpassword123"
            }
        ),
        responses={
            200: openapi.Response(
                description="Профиль обновлён",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                        "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                        "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя"),
                        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль (зашифрованный, не возвращается)"),
                        "favorites": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Описание продукта"),
                                    "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена продукта")
                                }
                            ),
                            description="Список избранных продуктов"
                        )
                    }
                )
            )
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить профиль пользователя",
        operation_description="Частично обновляет данные профиля текущего аутентифицированного пользователя.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Новый пароль пользователя")
            },
            example={
                "name": "Алексей",
                "phone_number": "+998901234567"
            }
        ),
        responses={
            200: openapi.Response(
                description="Профиль частично обновлён",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
                        "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                        "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                        "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя"),
                        "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя"),
                        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль (зашифрованный, не возвращается)"),
                        "favorites": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Описание продукта"),
                                    "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена продукта")
                                }
                            ),
                            description="Список избранных продуктов"
                        )
                    }
                )
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

class ToggleFavoriteAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Добавить/удалить продукт из избранного",
        operation_description="Добавляет продукт в избранное пользователя, если он там ещё не находится, или удаляет его, если он уже в избранном.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product_id"],
            properties={
                "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта")
            },
            example={
                "product_id": 1
            }
        ),
        responses={
            200: openapi.Response(
                description="Статус операции",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об успехе"),
                        "added": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Добавлен ли продукт в избранное"),
                        "favorites": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Описание продукта"),
                                    "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена продукта")
                                }
                            ),
                            description="Список избранных продуктов"
                        )
                    },
                    example={
                        "message": "Product added to favorites",
                        "added": True,
                        "favorites": [
                            {
                                "id": 1,
                                "name": "Product Name",
                                "description": "Product Description",
                                "price": 100.00
                            }
                        ]
                    }
                )
            ),
            404: "Продукт не найден"
        }
    )
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        user = request.user

        if product in user.favorites.all():
            user.favorites.remove(product)
            favorites = user.favorites.all()
            serializer = ProductSerializers(favorites, many=True)
            return Response({
                "message": "Product removed from favorites",
                "added": False,
                "favorites": serializer.data
            }, status=200)
        else:
            user.favorites.add(product)
            favorites = user.favorites.all()
            serializer = ProductSerializers(favorites, many=True)
            return Response({
                "message": "Product added to favorites",
                "added": True,
                "favorites": serializer.data
            }, status=200)

class LogoutAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Выход пользователя",
        operation_description="Завершает сессию пользователя, добавляя refresh-токен в чёрный список.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh-токен пользователя")
            },
            example={
                "refresh": "refresh_token_example"
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешный выход",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об успехе")
                    },
                    example={
                        "message": "Successfully logged out"
                    }
                )
            ),
            400: "Ошибка при выходе"
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)