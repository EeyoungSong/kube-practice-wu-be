from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from lingua_management.models import Category
from lingua_management.serializers.category_serializers import CategorySerializer

class CategoryListView(APIView):
    """
    카테고리 목록을 조회하는 View
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="카테고리 목록 조회"
    )
    def get(self, request):
        language = request.GET.get('language', 'en')

        categories = Category.objects.filter(user=request.user, language=language)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
