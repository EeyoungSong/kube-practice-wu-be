from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Sentence, Category
from ..serializers.sentence_serializers import SentenceSerializer
from ..serializers.category_serializers import CategorySerializer


class CategorySentencesView(APIView):
    """
    카테고리별 문장 조회 View
    - GET: 특정 카테고리에 속한 모든 문장 조회
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'category_id',
                openapi.IN_PATH,
                description="카테고리 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="카테고리별 문장 목록 조회",
        responses={
            200: openapi.Response(
                description="카테고리 정보와 해당 카테고리의 모든 문장 목록",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'category': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'sentences': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'text': openapi.Schema(type=openapi.TYPE_STRING),
                                    'meaning': openapi.Schema(type=openapi.TYPE_STRING),
                                    'words': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                'text': openapi.Schema(type=openapi.TYPE_STRING),
                                                'meaning': openapi.Schema(type=openapi.TYPE_STRING),
                                            }
                                        )
                                    ),
                                    'last_reviewed_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'review_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'is_last_review_successful': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        ),
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 문장 개수")
                    }
                )
            ),
            404: openapi.Response(description="카테고리를 찾을 수 없음")
        }
    )
    def get(self, request, category_id):
        """
        특정 카테고리에 속한 모든 문장을 조회합니다.
        Wordbook을 통해 카테고리와 연결된 문장들을 찾습니다.
        """
        user = request.user
        
        # 카테고리 존재 확인
        category = Category.objects.filter(user=user, id=category_id).first()
        if not category:
            return Response(
                {'error': '카테고리를 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 해당 카테고리에 속한 워드북들의 모든 문장을 조회
        sentences = Sentence.objects.filter(
            user=user,
            wordbook__category=category
        ).prefetch_related('word_links__word').order_by('created_at')
        
        # 시리얼라이즈
        category_serializer = CategorySerializer(category)
        sentence_serializer = SentenceSerializer(sentences, many=True)
        
        return Response({
            'category': category_serializer.data,
            'sentences': sentence_serializer.data,
            'total_count': sentences.count()
        }, status=status.HTTP_200_OK)


class SentenceManageView(APIView):
    """
    문장과 관련된 기능을 관리하는 View
    - GET: 문장 정보와 관련된 예문 리스트 조회
    - DELETE: 문장 삭제
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'sentence_id',
                openapi.IN_PATH,
                description="문장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="문장 삭제"
    )
    def delete(self, request, sentence_id):
        user = request.user
        sentence = Sentence.objects.filter(user=user, id=sentence_id).first()
        if not sentence:
            return Response({'error': '문장을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        sentence.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
    
