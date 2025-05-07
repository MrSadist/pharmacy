from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'surname', 'phone_number', 'avatar']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.role == 'specialist':
            return {
                'id': representation['id'],
                'email': representation['email'],
                'name': representation['name'],
                'surname': representation['surname']
            }
        return representation

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    avatar = serializers.ImageField(required=False)
    role = serializers.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=False, default='user')

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'surname', 'phone_number', 'password', 'avatar', 'role']
        extra_kwargs = {
            'avatar': {'required': False},
            'phone_number': {'required': True}
        }

    def create(self, validated_data):
        role = validated_data.pop('role', 'user')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            phone_number=validated_data['phone_number'],
            avatar=validated_data.get('avatar', None),
            role=role,
            is_staff=(role == 'specialist'),
            is_superuser=(role == 'specialist')
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    favorites = serializers.SerializerMethodField()

    def get_favorites(self, obj):
        from products.serializers import ProductSerializers
        return ProductSerializers(obj.favorites, many=True, read_only=True).data

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'surname', 'avatar', 'password', 'favorites']
        extra_kwargs = {
            'avatar': {'required': False},
            'email': {'required': False},
            'phone_number': {'required': False}
        }

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.name = validated_data.get('name', instance.name)
        instance.surname = validated_data.get('surname', instance.surname)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.avatar = validated_data.get('avatar', instance.avatar)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ExtendedUserSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = ['id', 'email', 'name', 'surname', 'phone_number', 'avatar', 'role']


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'surname', 'phone_number', 'avatar', 'role', 'password', 'is_active', 'is_staff',
                  'is_superuser']
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
            'surname': {'required': False},
            'phone_number': {'required': False},
            'avatar': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance