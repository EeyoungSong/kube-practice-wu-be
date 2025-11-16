from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Word, SentenceWord, Category, Wordbook
from ..serializers.word_serializers import WordExampleSerializer, WordSerializer
from ..serializers.category_serializers import CategorySerializer
from logging import getLogger

logger = getLogger(__name__)


class CategoryWordsView(APIView):
    """
    카테고리별 단어 조회 View
    - GET: 특정 카테고리에 속한 모든 단어 조회
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
        operation_summary="카테고리별 단어 목록 조회",
        responses={
            200: openapi.Response(
                description="카테고리 정보와 해당 카테고리의 모든 단어 목록",
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
                        'words': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'text': openapi.Schema(type=openapi.TYPE_STRING),
                                    'last_reviewed_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'review_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'is_last_review_successful': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                }
                            )
                        ),
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 단어 개수")
                    }
                )
            ),
            404: openapi.Response(description="카테고리를 찾을 수 없음")
        }
    )
    def get(self, request, category_id):
        """
        특정 카테고리에 속한 모든 단어를 조회합니다.
        Wordbook을 통해 카테고리와 연결된 단어들을 찾습니다.
        """
        user = request.user
        
        # 카테고리 존재 확인
        category = Category.objects.filter(user=user, id=category_id).first()
        if not category:
            return Response(
                {'error': '카테고리를 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 해당 카테고리에 속한 워드북들의 문장들에서 나온 모든 단어를 조회
        words = Word.objects.filter(
            user=user,
            sentence_links__sentence__wordbook__category=category
        ).distinct().order_by('text')
        
        # 시리얼라이즈
        category_serializer = CategorySerializer(category)
        word_serializer = WordSerializer(words, many=True)
        
        return Response({
            'category': category_serializer.data,
            'words': word_serializer.data,
            'total_count': words.count()
        }, status=status.HTTP_200_OK)


class WordManageView(APIView):
    """
    단어와 관련된 기능을 관리하는 View
    - GET: 단어 정보와 관련된 예문 리스트 조회
    - DELETE: 단어 삭제
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'word_id',
                openapi.IN_PATH,
                description="단어 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="단어 정보 및 관련 예문 조회",
        responses={
            200: openapi.Response(
                description="단어 정보와 관련 예문 목록",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'word': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'text': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_reviewed_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                'review_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'is_last_review_successful': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        ),
                        'sentences': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'sentence': openapi.Schema(type=openapi.TYPE_OBJECT),
                                    'meaning': openapi.Schema(type=openapi.TYPE_STRING, description="해당 문장에서의 단어의 뜻")
                                }
                            )
                        )
                    }
                )
            ),
            404: openapi.Response(description="단어를 찾을 수 없음")
        }
    )
    def get(self, request, word_id):
        """
        특정 단어의 정보와 해당 단어가 포함된 모든 문장을 조회합니다.
        """
        user = request.user
        word = Word.objects.filter(user=user, id=word_id).first()
        
        if not word:
            return Response(
                {'error': '단어를 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        logger.info("word", word)
        # 단어 정보 시리얼라이즈
        word_serializer = WordSerializer(word)
        logger.info("word_serializer", word_serializer.data)

        # 해당 단어가 포함된 모든 문장과 문맥별 뜻 조회
        sentence_words = SentenceWord.objects.filter(word=word).select_related('sentence')
        sentence_serializer = WordExampleSerializer(sentence_words, many=True)
        
        return Response({
            'word': word_serializer.data,
            'sentences': sentence_serializer.data
        }, status=status.HTTP_200_OK)
        
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'word_id',
                openapi.IN_PATH,
                description="단어 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="단어 삭제"
    )
    def delete(self, request, word_id):
        user = request.user
        wordSentence = SentenceWord.objects.filter(word=word_id)
        if not wordSentence:
            return Response({'error': '단어를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        wordSentence.delete()

        # word에 연결된 wordSentence가 없으면 word 삭제
        if not SentenceWord.objects.filter(word=word_id).exists():
            word = Word.objects.filter(user=user, id=word_id).first()
            if word:
                word.delete()

        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)

class WordContextWithTextView(APIView):
    """
    단어 문맥 조회 View
    - GET: 단어 문맥 조회
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'word',
                openapi.IN_QUERY,
                description="문맥을 조회할 단어 텍스트",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        operation_summary="단어 문맥 조회",
        responses={
            200: openapi.Response(description="단어와 연관된 문장 목록"),
            400: openapi.Response(description="필수 쿼리 파라미터 누락"),
        },
    )
    def get(self, request):
        user = request.user
        word_text = request.query_params.get('word')

        if not word_text:
            return Response({'error': 'word parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        word = Word.objects.filter(user=user, text=word_text).first()
        if not word:
            return Response({'success': True, 'sentences': []}, status=status.HTTP_200_OK)
        
        sentence_words = SentenceWord.objects.filter(word=word)
        sentence_serializer = WordExampleSerializer(sentence_words, many=True)
        return Response({'success': True, 'sentences': sentence_serializer.data}, status=status.HTTP_200_OK)
