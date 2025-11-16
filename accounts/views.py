from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_yasg.utils import swagger_auto_schema  
from drf_yasg import openapi
from django.conf import settings
from .serializers import SignupSerializer, LoginSerializer, GoogleAuthSerializer, GoogleUserSerializer, UserSerializer
from .models import GoogleUser
import json
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import logging

logger = logging.getLogger(__name__)
# Create your views here.


class SignupView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=SignupSerializer,
        operation_summary="이메일/비밀번호 회원가입",
        responses={
            201: openapi.Response(description='회원가입 성공'),
            400: openapi.Response(description='유효하지 않은 요청 데이터'),
        },
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        operation_summary="JWT 로그인",
        responses={
            200: openapi.Response(description='로그인 성공 및 토큰 반환'),
            400: openapi.Response(description='유효하지 않은 인증 정보'),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            
            response = Response({
                'success': True,
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_200_OK)
            
            # Refresh 토큰을 HTTP-only 쿠키로 설정
            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS에서만 전송 (프로덕션)
                samesite='Lax'
            )
            
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="로그아웃 및 Refresh 토큰 무효화",
        responses={
            200: openapi.Response(description='로그아웃 성공'),
            400: openapi.Response(description='잘못된 토큰'),
            500: openapi.Response(description='서버 오류'),
        },
    )
    def post(self, request):
        try:
            # 쿠키에서 refresh 토큰 가져오기
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                # 토큰을 블랙리스트에 추가
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            response = Response({'success': True}, status=status.HTTP_200_OK)
            
            # 쿠키에서 refresh 토큰 삭제
            response.delete_cookie('refresh_token')
            
            return response
            
        except TokenError:
            response = Response({'error': '잘못된 토큰입니다.'}, status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie('refresh_token')  # 잘못된 토큰이라면 쿠키 삭제
            return response
        except Exception as e:
            return Response({'error': '로그아웃 처리 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenRefreshView(APIView):
    """
    쿠키에서 refresh token을 읽어 새로운 access token을 발급하는 커스텀 뷰
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Refresh 토큰으로 Access 토큰 재발급",
        responses={
            200: openapi.Response(description='새로운 액세스 토큰 반환'),
            401: openapi.Response(description='Refresh 토큰 없음/만료'),
            500: openapi.Response(description='서버 오류'),
        },
    )
    def post(self, request):
        try:
            # 쿠키에서 refresh 토큰 가져오기
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'Refresh token이 없습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 새로운 access token 생성
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            
            response = Response({
                'success': True,
                'access': str(new_access_token)
            }, status=status.HTTP_200_OK)
            
            # 토큰 회전이 활성화된 경우 새로운 refresh token도 발급
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                refresh.set_jti()
                refresh.set_exp()
                response.set_cookie(
                    'refresh_token',
                    str(refresh),
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='Lax'
                )
            
            return response
            
        except TokenError as e:
            response = Response({'error': '잘못된 또는 만료된 refresh token입니다.'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie('refresh_token')  # 잘못된 토큰이라면 쿠키 삭제
            return response
        except Exception as e:
            return Response({'error': '토큰 새로고침 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileManagementView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="프로필 관리",
        responses={
            200: openapi.Response(description='프로필 관리 성공'),
        },
    )
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    """
    구글 OAuth2 로그인 URL을 제공하는 뷰
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="구글 OAuth2 로그인 URL 생성",
        responses={
            200: openapi.Response(description='구글 인증 URL 반환'),
            500: openapi.Response(description='구글 OAuth 구성 오류'),
        },
    )
    def get(self, request):
        try:
            # Google OAuth2 Flow 설정
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=['openid', 'email', 'profile']
            )
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            
            # 인증 URL 생성
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # 상태값을 세션에 저장 (CSRF 보호)
            request.session['oauth_state'] = state
            
            return Response({
                'authorization_url': authorization_url,
                'state': state
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Google OAuth2 URL 생성 오류: {str(e)}")
            return Response({'error': '구글 로그인 URL 생성에 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleCallbackView(APIView):
    """
    구글 OAuth2 콜백을 처리하는 뷰
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        request_body=GoogleAuthSerializer,
        operation_summary="구글 OAuth2 콜백 처리",
        responses={
            200: openapi.Response(description='로그인 성공 및 토큰 반환'),
            400: openapi.Response(description='잘못된 요청 데이터'),
            500: openapi.Response(description='구글 인증 처리 실패'),
        },
    )
    def post(self, request):
        try:
            serializer = GoogleAuthSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            code = serializer.validated_data['code']
            
            # Google OAuth2 Flow 설정
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI]
                    }
                },
                scopes=['openid', 'email', 'profile']
            )
            flow.redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
            
            # Authorization code로 토큰 교환
            flow.fetch_token(code=code)
            
            # ID 토큰 검증 및 사용자 정보 추출
            credentials = flow.credentials
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            # 사용자 정보 추출
            google_id = id_info['sub']
            google_email = id_info['email']
            name = id_info.get('name', '')
            picture = id_info.get('picture', '')
            
            # 기존 구글 사용자 확인
            try:
                google_user = GoogleUser.objects.get(google_id=google_id)
                user = google_user.user
                created = False
            except GoogleUser.DoesNotExist:
                # 이메일로 기존 사용자 확인
                try:
                    user = User.objects.get(email=google_email)
                    # 기존 사용자에게 구글 계정 연결
                    google_user = GoogleUser.objects.create(
                        user=user,
                        google_id=google_id,
                        google_email=google_email,
                        picture=picture
                    )
                    created = False
                except User.DoesNotExist:
                    # 새 사용자 생성
                    username = google_email.split('@')[0]
                    
                    # 중복 username 처리
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1
                    
                    user = User.objects.create_user(
                        username=username,
                        email=google_email,
                        first_name=name.split(' ')[0] if name else '',
                        last_name=' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
                    )
                    
                    google_user = GoogleUser.objects.create(
                        user=user,
                        google_id=google_id,
                        google_email=google_email,
                        picture=picture
                    )
                    created = True
            
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            
            response = Response({
                'success': True,
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'created': created,
                'google_user': GoogleUserSerializer(google_user).data
            }, status=status.HTTP_200_OK)
            
            # Refresh 토큰을 HTTP-only 쿠키로 설정
            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Google OAuth2 콜백 처리 오류: {str(e)}")
            return Response({'error': '구글 로그인 처리 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleUserInfoView(APIView):
    """
    현재 로그인한 사용자의 구글 계정 정보를 조회하는 뷰
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="구글 계정 연동 정보 조회",
        responses={
            200: openapi.Response(description='구글 사용자 정보 반환'),
            404: openapi.Response(description='연동되지 않은 사용자'),
        },
    )
    def get(self, request):
        try:
            google_user = GoogleUser.objects.get(user=request.user)
            serializer = GoogleUserSerializer(google_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except GoogleUser.DoesNotExist:
            return Response({'error': '구글 계정이 연결되지 않은 사용자입니다.'}, status=status.HTTP_404_NOT_FOUND)
    
