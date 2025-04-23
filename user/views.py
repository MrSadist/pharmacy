from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, RegisterSerializer, UserProfileSerializer, LoginSerializer, OTPSerializer
from products.models import Product
from products.serializers import ProductSerializers
from django.core.mail import send_mail
from django.conf import settings
import random
from datetime import timedelta
from .models import CustomUser
from django.utils import timezone

class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        operation_description="Создаёт нового пользователя с указанным email, именем, фамилией, номером телефона и паролем, после чего отправляет OTP-код на email для верификации.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "name", "surname", "phone_number", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Электронная почта пользователя"),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                "surname": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия пользователя"),
                "phone_number": openapi.Schema(type=openapi.TYPE_STRING, description="Номер телефона пользователя (например, +998901234567)"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль пользователя"),
                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя (опционально)")
            },
            example={
                "email": "user@example.com",
                "name": "Иван",
                "surname": "Иванов",
                "phone_number": "+998901234567",
                "password": "securepassword123",
                "avatar": "https://example.com/avatar.jpg"
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
                                "avatar": openapi.Schema(type=openapi.TYPE_STRING, format="uri", description="URL аватара пользователя")
                            }
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об успехе")
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
                        "message": "User created. OTP sent to email."
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерация и сохранение OTP
        otp = str(random.randint(100000, 999999))
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save()

        # Отправка письма
        send_mail(
            'Your Verification Code',
            f'Your OTP code is: {otp}. The code is valid for 5 minutes.',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        return Response({
            'user': UserSerializer(user).data,
            'message': 'User created. OTP sent to email.'
        }, status=201)

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
                "language": openapi.Schema(type=openapi.TYPE_STRING, description="Язык (uz, ru, en)", default="en")
            },
            example={
                "email": "user@example.com",
                "password": "securepassword123",
                "language": "en"
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
                        "added": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Добавлен ли продукт в избранное")
                    },
                    example={
                        "message": "Product added to favorites",
                        "added": True
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
            return Response({"message": "Product removed from favorites", "added": False}, status=200)
        else:
            user.favorites.add(product)
            return Response({"message": "Product added to favorites", "added": True}, status=200)

class FavoriteProductsAPI(generics.ListAPIView):
    serializer_class = ProductSerializers
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.favorites.all()

    @swagger_auto_schema(
        operation_summary="Получить список избранных продуктов",
        operation_description="Возвращает список всех продуктов, которые пользователь добавил в избранное.",
        responses={
            200: openapi.Response(
                description="Список избранных продуктов",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID продукта"),
                            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Название продукта"),
                            "description": openapi.Schema(type=openapi.TYPE_STRING, description="Описание продукта"),
                            "price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Цена продукта")
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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