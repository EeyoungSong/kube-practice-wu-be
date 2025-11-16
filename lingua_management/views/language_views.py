from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from lingua_management.models import Language
from lingua_management.serializers.language_serializers import LanguageSerializer
from lingua_management.models import CustomUserLanguageMapping

class LanguageListView(APIView):
    """
    언어 목록을 조회하는 View
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="언어 목록 조회"
    )
    def get(self, request):
        user = request.user
        custom_user_language_mapping = CustomUserLanguageMapping.objects.filter(user=user)
        languages = [custom_user_language_mapping.language for custom_user_language_mapping in custom_user_language_mapping]

        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)
