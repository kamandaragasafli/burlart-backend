from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VideoGeneration, ImageGeneration

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'credits', 'language', 'theme']
        extra_kwargs = {
            'credits': {'read_only': True},
        }
    
    def create(self, validated_data):
        # New users start with 0 credits
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            language=validated_data.get('language', 'en'),
            theme=validated_data.get('theme', 'dark'),
            credits=0,  # Start with 0 credits
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'credits', 'language', 'theme']


class VideoGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoGeneration
        fields = [
            'id', 'prompt', 'tool', 'model_id', 'credits_used', 
            'status', 'video_url', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'video_url', 'error_message', 'created_at', 'updated_at']


class VideoGenerationCreateSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=2000)
    tool = serializers.ChoiceField(choices=VideoGeneration.TOOL_CHOICES)
    options = serializers.DictField(required=False, allow_null=True)


class ImageGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageGeneration
        fields = [
            'id', 'prompt', 'tool', 'model_id', 'credits_used', 
            'status', 'image_url', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'image_url', 'error_message', 'created_at', 'updated_at']


class ImageGenerationCreateSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=2000)
    tool = serializers.ChoiceField(choices=ImageGeneration.TOOL_CHOICES)
    options = serializers.DictField(required=False, allow_null=True)
