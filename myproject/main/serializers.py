from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, UserProfile, Notification


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError({"error": "Invalid credentials"})
        if not user.is_active:
            raise serializers.ValidationError({"error": "User account is disabled"})
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'email',
            'full_name',
            'contact_number',
            'resume_url',
            'skills',
            'experience',
            'education',
            'profile_picture_url',
        ]

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be provided as a list")
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data


class NotificationSerializer(serializers.ModelSerializer):
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'recipient_username',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'related_object_id',
            'related_object_type'
        ]
        read_only_fields = ['id', 'recipient', 'notification_type', 'title', 'message', 'created_at']