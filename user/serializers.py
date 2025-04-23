from rest_framework import serializers
from .models import CustomUser
from products.serializers import ProductSerializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'surname', 'phone_number', 'avatar']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'surname', 'phone_number', 'password', 'avatar']
        extra_kwargs = {
            'avatar': {'required': False},
            'phone_number': {'required': True}
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            surname=validated_data['surname'],
            phone_number=validated_data['phone_number'],
            avatar=validated_data.get('avatar', None),
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    favorites = ProductSerializers(many=True, read_only=True)

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