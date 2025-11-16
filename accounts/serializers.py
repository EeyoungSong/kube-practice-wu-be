from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from .models import GoogleUser

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('이미 존재하는 이메일입니다.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']  # 이제 필수로 받음
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # 이메일로 사용자 찾기
            try:
                user = User.objects.get(email=email)
                # 찾은 사용자의 username으로 인증
                user = authenticate(username=user.username, password=password)
                if user:
                    if user.is_active:
                        attrs['user'] = user
                        return attrs
                    else:
                        raise serializers.ValidationError('사용자 계정이 비활성화되었습니다.')
                else:
                    raise serializers.ValidationError('잘못된 이메일 또는 비밀번호입니다.')
            except User.DoesNotExist:
                raise serializers.ValidationError('잘못된 이메일 또는 비밀번호입니다.')
        else:
            raise serializers.ValidationError('이메일과 비밀번호를 모두 입력해주세요.')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError('잘못된 토큰입니다.')

class GoogleAuthSerializer(serializers.Serializer):
    """
    구글 OAuth2 인증을 위한 Serializer
    """
    code = serializers.CharField(help_text="구글에서 받은 authorization code")
    
    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError('Authorization code가 필요합니다.')
        return value

class GoogleUserSerializer(serializers.ModelSerializer):
    """
    구글 사용자 정보 조회를 위한 Serializer
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = GoogleUser
        fields = ['google_id', 'google_email', 'picture', 'username', 'email', 'created_at']
        read_only_fields = ['google_id', 'google_email', 'picture', 'created_at']