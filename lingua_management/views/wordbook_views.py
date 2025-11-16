from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from ..models import Category, Wordbook, Sentence, Word, SentenceWord
from ..serializers.wordbook_serializers import CommitSelectionSerializer, WordbookUpdateSerializer, WordbookSerializer

import logging

logger = logging.getLogger(__name__)

logger.info(">>> runserver 테스트")

class WordbookListView(APIView):
    """
    사용자의 단어장 목록을 조회하는 View
    - 카테고리가 없으면 모든 단어장 조회
    - 카테고리가 있으면 해당 카테고리의 단어장만 조회
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'category_id',
                openapi.IN_QUERY,
                description="카테고리 ID (선택사항). 없으면 모든 단어장 조회, 있으면 해당 카테고리의 단어장만 조회",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        operation_summary="사용자의 단어장 목록 조회 (카테고리 필터링 지원)",
        responses={
            200: openapi.Response(
                description="단어장 목록 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'wordbooks': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        ),
                        'category': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="필터링된 카테고리 정보 (category_id가 제공된 경우만)",
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 단어장 개수")
                    }
                )
            ),
            404: openapi.Response(description="카테고리를 찾을 수 없음")
        }
    )
    def get(self, request):
        """
        사용자의 단어장을 조회합니다.
        카테고리 ID가 제공되면 해당 카테고리의 단어장만, 없으면 모든 단어장을 조회합니다.
        """
        
        user = request.user
        category_id = request.GET.get('category_id')
        
        
        # 기본 쿼리셋
        wordbooks = Wordbook.objects.filter(user=user)
        logger.info(f"wordbooks: {wordbooks}")
        
        category_info = None
        
        # 카테고리 필터링
        if category_id:
            try:
                category_id = int(category_id)
                category = Category.objects.filter(user=user, id=category_id).first()
                
                if not category:
                    return Response(
                        {'error': '카테고리를 찾을 수 없습니다.'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                wordbooks = wordbooks.filter(category=category)
                category_info = {'id': category.id, 'name': category.name}
                
            except ValueError:
                return Response(
                    {'error': '올바른 카테고리 ID를 입력해주세요.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 정렬
        wordbooks = wordbooks.order_by('-created_at')
        
        # 시리얼라이즈
        serializer = WordbookSerializer(wordbooks, many=True)
        
        response_data = {
            'wordbooks': serializer.data,
            'total_count': wordbooks.count()
        }
        
        # 카테고리 정보가 있으면 추가
        if category_info:
            response_data['category'] = category_info
            
        return Response(response_data, status=status.HTTP_200_OK)


class WordbookCreateView(APIView):
    """
    단어장(노트)을 생성(저장)하는 View
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=CommitSelectionSerializer,
        operation_summary="분석된 단어/문장을 새 노트에 저장"
    )
    def post(self, request):
        """
        사용자가 선택한 단어와 문장을 새로운 단어장에 저장합니다.
        """
        serializer = CommitSelectionSerializer(data=request.data) # 형식 검증
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data # 직렬화
        
        user = request.user
        
        logger.info(f"data: {data}")
        
        try:
            now = timezone.now()
            category, _ = Category.objects.get_or_create(
                user=user, name=data['category'], language=data['language']
            )
            
            wordbook = Wordbook.objects.create(
                user=user,
                name=data['name'],
                category=category,
                language=data['language'],
                input_type=data['input_type'],  
                created_at=now
            )
            
            for sent in data['sentences']:
                sentence = Sentence.objects.create(
                    user=user,
                    wordbook=wordbook,
                    text=sent['text'],
                    meaning=sent.get('meaning', ''),
                    created_at=now
                )
                for word in sent['words']:
                    word_obj, created = Word.objects.get_or_create(
                        user=user,
                        text=word['text'].lower(),
                        defaults={
                            'others': word.get('others', ''),
                            'created_at': now
                        }
                    )
                    
                    # 기존 단어인 경우에도 others 필드 업데이트 (새로운 발음 정보가 있을 수 있음)
                    if not created and word.get('others'):
                        word_obj.others = word.get('others', '')
                        word_obj.save()
                    
                    SentenceWord.objects.create(
                        word=word_obj,
                        sentence=sentence,
                        meaning=word.get('meaning', ''),
                        pos=word.get('pos', ''),
                        memo=word.get('memo', ''),
                    )
                    
        except IntegrityError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({'success': True, 'wordbook_id': wordbook.id}, status=status.HTTP_201_CREATED)


class WordbookDetailView(APIView):
    """
    단어장(노트)을 조회, 수정, 삭제하는 View
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'wordbook_id',
                openapi.IN_PATH,
                description="단어장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="단어장(노트) 상세 정보 조회"
    )
    def get(self, request, wordbook_id):
        logger.info(f"wordbook_id: {wordbook_id}")
        wordbook = get_object_or_404(Wordbook, user=request.user, id=wordbook_id)
        serializer = WordbookSerializer(wordbook)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'wordbook_id',
                openapi.IN_PATH,
                description="단어장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=WordbookUpdateSerializer,
        operation_summary="단어장(노트)의 이름 또는 카테고리 수정"
    )
    def patch(self, request, wordbook_id):
        wordbook = get_object_or_404(Wordbook, user=request.user, id=wordbook_id)
        serializer = WordbookUpdateSerializer(
            wordbook, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'wordbook': serializer.data}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'wordbook_id',
                openapi.IN_PATH,
                description="단어장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="단어장(노트) 삭제"
    )
    def delete(self, request, wordbook_id):   
        wordbook = get_object_or_404(Wordbook, user=request.user, id=wordbook_id)
        wordbook.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 기존 호환성을 위해 유지 (deprecated)
class WordbookManageView(APIView):
    """
    단어장(노트)을 생성(저장)하고, 수정하고, 삭제하는 View
    - 호환성을 위해 유지되지만, WordbookCreateView와 WordbookDetailView 사용을 권장합니다.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=CommitSelectionSerializer,
        operation_summary="분석된 단어/문장을 새 노트에 저장"
    )
    def post(self, request):
        """
        사용자가 선택한 단어와 문장을 새로운 단어장에 저장합니다.
        """
        create_view = WordbookCreateView()
        create_view.request = request
        return create_view.post(request)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'wordbook_id',
                openapi.IN_PATH,
                description="단어장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="단어장(노트) 상세 정보 조회"
    )
    def get(self, request, wordbook_id):
        detail_view = WordbookDetailView()
        detail_view.request = request
        return detail_view.get(request, wordbook_id)
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'wordbook_id',
                openapi.IN_PATH,
                description="단어장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=WordbookUpdateSerializer,
        operation_summary="단어장(노트)의 이름 또는 카테고리 수정"
    )
    def patch(self, request, wordbook_id):
        detail_view = WordbookDetailView()
        detail_view.request = request
        return detail_view.patch(request, wordbook_id)
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'wordbook_id',
                openapi.IN_PATH,
                description="단어장 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_summary="단어장(노트) 삭제"
    )
    def delete(self, request, wordbook_id):
        detail_view = WordbookDetailView()
        detail_view.request = request
        return detail_view.delete(request, wordbook_id)
    
    