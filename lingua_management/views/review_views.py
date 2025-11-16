from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

from lingua_management.models import SentenceWord, Wordbook, Category, Word
from lingua_management.serializers.word_serializers import (
    ReviewDataSerializer,
    ReviewSubmissionSerializer,
)


class GraphDataView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description='가져올 노드 수 (기본값 200, 0이면 비어있는 결과)',
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                'offset',
                openapi.IN_QUERY,
                description='결과 시작 위치 (기본값 0)',
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        operation_summary='단어-문장 그래프 데이터 조회',
        responses={
            200: openapi.Response(description='그래프 데이터 (nodes, edges)'),
            400: openapi.Response(description='limit/offset 파라미터 오류'),
        },
    )
    def get(self, request):
        limit_param = request.query_params.get('limit')
        offset_param = request.query_params.get('offset')

        try:
            limit = int(limit_param) if limit_param is not None else 200
            offset = int(offset_param) if offset_param is not None else 0
        except (TypeError, ValueError):
            return Response(
                {'detail': 'limit and offset must be integers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if limit < 0 or offset < 0:
            return Response(
                {'detail': 'limit and offset must be non-negative.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sentence_words = (
            SentenceWord.objects.filter(word__user=request.user)
            .select_related('sentence', 'word')
            .order_by('id')
        )

        if limit == 0:
            sentence_words = sentence_words.none()
        else:
            end = offset + limit if limit is not None else None
            sentence_words = (
                sentence_words[offset:end]
                if end is not None
                else sentence_words[offset:]
            )

        word_nodes = {}
        sentence_nodes = {}
        edges = []

        for sentence_word in sentence_words:
            word = sentence_word.word
            sentence = sentence_word.sentence

            word_node_id = f"w{word.id}"
            sentence_node_id = f"s{sentence.id}"

            if word_node_id not in word_nodes:
                word_nodes[word_node_id] = {
                    'id': word_node_id,
                    'label': word.text,
                    'type': 'word',
                    'meaning': sentence_word.meaning or '',
                    'color': 'rgba(255,255,255,1)',
                }
            elif not word_nodes[word_node_id]['meaning'] and sentence_word.meaning:
                word_nodes[word_node_id]['meaning'] = sentence_word.meaning

            if sentence_node_id not in sentence_nodes:
                review_count = sentence.review_count or 0
                brightness = min(1, 0.2 + review_count * 0.2)
                sentence_nodes[sentence_node_id] = {
                    'id': sentence_node_id,
                    'label': sentence.text,
                    'type': 'sentence',
                    'review_count': review_count,
                    'color': f"rgba(177,156,217,{brightness:.2f})",
                }

            edges.append({'from': sentence_node_id, 'to': word_node_id})

        nodes = list(word_nodes.values()) + list(sentence_nodes.values())

        return Response({'nodes': nodes, 'edges': edges})


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'wordbook_id',
            openapi.IN_PATH,
            description='리뷰 데이터를 조회할 워드북 ID',
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            'limit',
            openapi.IN_QUERY,
            description='최대 반환 단어 수 (기본값 20)',
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            'reviewed',
            openapi.IN_QUERY,
            description="'true'는 복습 완료 단어만, 'false'는 미복습 단어만",
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    operation_summary='특정 워드북의 복습 단어 조회',
    responses={
        200: openapi.Response(description='리뷰 대상 단어 목록'),
        404: openapi.Response(description='워드북 없음'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wordbook_review_words_with_id(request, wordbook_id):
    """
    특정 wordbook의 리뷰용 단어 데이터를 반환합니다.
    wordbook 문장의 맥락 속의 의미를 제공합니다.
    
    Query Parameters:
    - limit: 반환할 단어 수 제한 (기본값: 20)
    - reviewed: 'true'면 복습한 단어만, 'false'면 복습 안한 단어만, 없으면 전체
    """
    user = request.user
    limit = int(request.GET.get('limit', 20))
    reviewed_filter = request.GET.get('reviewed')
    
    # wordbook 권한 확인
    try:
        wordbook = Wordbook.objects.get(id=wordbook_id, user=user)
    except Wordbook.DoesNotExist:
        return Response({
            'error': '해당 wordbook을 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # 기본 쿼리: 특정 wordbook의 SentenceWord들
    queryset = SentenceWord.objects.filter(
        sentence__wordbook=wordbook,
        word__user=user
    ).select_related('word', 'sentence')
    
    # 복습 상태 필터링
    if reviewed_filter == 'true':
        queryset = queryset.filter(word__review_count__gt=0)
    elif reviewed_filter == 'false':
        queryset = queryset.filter(word__review_count=0)
    
    # 전체 개수
    total_count = queryset.count()
    
    # 제한된 데이터를 랜덤으로 가져오기
    sentence_words = queryset.order_by('?')[:limit]
    
    # ReviewWord 형태로 데이터 변환
    review_words = []
    for sw in sentence_words:
        review_word = {
            'id': str(sw.id),
            'word': sw.word.text,
            'meaning': sw.meaning if sw.meaning else '',
            'others': sw.word.others if sw.word.others else '',
            'pos': sw.pos if sw.pos else '',
            'context': sw.sentence.text
        }
        review_words.append(review_word)
    
    # 응답 데이터 구성
    review_data = {
        'words': review_words,
        'total_count': total_count
    }
    
    serializer = ReviewDataSerializer(review_data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'category',
            openapi.IN_QUERY,
            description="카테고리 ID (all이면 전체)",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            'language',
            openapi.IN_QUERY,
            description='필터링할 언어 코드',
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            'limit',
            openapi.IN_QUERY,
            description='최대 반환 단어 수 (기본값 20)',
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            'reviewed',
            openapi.IN_QUERY,
            description="'true'는 복습 완료 단어만, 'false'는 미복습 단어만",
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    operation_summary='카테고리별 복습 단어 조회',
    responses={
        200: openapi.Response(description='리뷰 대상 단어 목록'),
        400: openapi.Response(description='잘못된 요청 파라미터'),
        404: openapi.Response(description='카테고리 없음'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wordbook_review_words(request):
    """
    특정 category의 리뷰용 단어 데이터를 반환합니다.
    단어에 맵핑되어 있는 여러 의미를 제공합니다.
    
    Query Parameters:
    - category_id: 카테고리 ID ('all'이면 전체 카테고리)
    - limit: 반환할 단어 수 제한 (기본값: 20)
    - reviewed: 'true'면 복습한 단어만, 'false'면 복습 안한 단어만, 없으면 전체
    """
    user = request.user
    category_id = request.GET.get('category')
    language = request.GET.get('language')
    limit = int(request.GET.get('limit', 20))
    reviewed_filter = request.GET.get('reviewed')

    logger.info(f"get_wordbook_review_words called by user: {user.username}")
    logger.info(f"Parameters - category_id: {category_id}, language: {language}, limit: {limit}, reviewed: {reviewed_filter}")

    # 카테고리 필터링
    if category_id and category_id != "all":
        try:
            category_id = int(category_id)
            category = Category.objects.get(id=category_id, user=user)
            logger.info(f"Found category: {category.name} (id: {category.id}, language: {category.language})")
            
            # Category의 language와 요청된 language가 일치하는지 확인
            if language and category.language != language:
                logger.warning(f"Language mismatch: category.language={category.language}, requested={language}")
                return Response({
                    'error': f'Category language ({category.language}) does not match requested language ({language})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 해당 카테고리의 단어들을 직접 필터링 (더 효율적)
            word_queryset = Word.objects.filter(
                user=user,
                sentence_links__sentence__wordbook__category=category
            )
            
            if language:
                word_queryset = word_queryset.filter(
                    sentence_links__sentence__wordbook__language=language
                )
            
            logger.info(f"Word queryset count before distinct: {word_queryset.count()}")
            
        except (ValueError, TypeError):
            logger.error(f"Invalid category_id format: {request.GET.get('category_id')}")
            return Response({'error': 'Invalid category_id format'}, status=status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            logger.error(f"Category not found: id={category_id}, user={user.username}")
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        logger.info("Filtering all categories")
        word_queryset = Word.objects.filter(user=user)
        if language:
            word_queryset = word_queryset.filter(
                sentence_links__sentence__wordbook__language=language
            )

    # 복습 상태 필터링
    if reviewed_filter == 'true':
        word_queryset = word_queryset.filter(review_count__gt=0)
        logger.info(f"Filtering reviewed words (review_count > 0)")
    elif reviewed_filter == 'false':
        word_queryset = word_queryset.filter(review_count=0)
        logger.info(f"Filtering unreviewed words (review_count = 0)")

    # 전체 개수 계산 (제한 적용 전)
    total_count = word_queryset.distinct().count()
    logger.info(f"Total distinct words found: {total_count}")
    
    # 제한된 데이터를 랜덤으로 가져오기
    word_queryset = word_queryset.distinct().order_by('?')[:limit]
    logger.info(f"Selected {len(word_queryset)} words after limit and random ordering")

    # N+1 문제 해결을 위한 prefetch_related 사용
    words_with_meanings = word_queryset.prefetch_related(
        'sentence_links__sentence',
        'sentence_links__sentence__wordbook',
        'sentence_links__sentence__wordbook__category'
    )

    review_words = []
    for word in words_with_meanings:
        # 해당 단어의 모든 의미들 수집
        sentence_words = word.sentence_links.all()
        
        meanings = []
        for sentence_word in sentence_words:
            meanings.append({
                'id': str(sentence_word.id),
                'meaning': sentence_word.meaning if sentence_word.meaning else '',
                'others': word.others if word.others else '',
                'pos': sentence_word.pos if sentence_word.pos else '',
                'context': sentence_word.sentence.text,
            })
        
        review_words.append({
            'word': word.text,
            'meanings': meanings
        })
    
    # 응답 데이터 구성
    review_data = {
        'words': review_words,
        'total_count': total_count
    }
    
    serializer = ReviewDataSerializer(review_data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'word_id',
            openapi.IN_PATH,
            description='복습 완료로 표시할 SentenceWord ID',
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'is_successful': openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description='복습 성공 여부 (기본값 true)',
            ),
        },
    ),
    operation_summary='단어 복습 완료 처리',
    responses={
        200: openapi.Response(description='복습 완료 처리 결과'),
        404: openapi.Response(description='단어 없음'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_word_reviewed(request, word_id):
    """
    특정 단어를 복습 완료로 표시합니다.
    
    Body:
    - is_successful: boolean (복습 성공 여부)
    """
    user = request.user
    is_successful = request.data.get('is_successful', True)
    
    try:
        sentence_word = SentenceWord.objects.get(
            id=word_id,
            word__user=user
        )
        
        # 단어의 복습 정보 업데이트
        word = sentence_word.word
        word.review_count += 1
        word.is_last_review_successful = is_successful
        from django.utils import timezone
        word.last_reviewed_at = timezone.now()
        word.save()
        
        return Response({
            'message': '복습 완료로 표시되었습니다.',
            'review_count': word.review_count
        }, status=status.HTTP_200_OK)
        
    except SentenceWord.DoesNotExist:
        return Response({
            'error': '해당 단어를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'wordbook_id',
            openapi.IN_PATH,
            description='리뷰 결과를 제출할 워드북 ID',
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
    request_body=ReviewSubmissionSerializer,
    operation_summary='워드북 리뷰 결과 제출',
    responses={
        200: openapi.Response(description='리뷰 결과 처리 성공'),
        400: openapi.Response(description='잘못된 요청 데이터'),
        404: openapi.Response(description='워드북 없음'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_wordbook_review(request, wordbook_id):
    """
    특정 wordbook의 리뷰 결과를 제출합니다.
    
    Body:
    {
        "wordbook_id": 12,
        "results": [
            {"word_id": "1", "is_known": true},
            {"word_id": "2", "is_known": false}
        ]
    }
    """
    user = request.user
    
    # wordbook 권한 확인
    try:
        wordbook = Wordbook.objects.get(id=wordbook_id, user=user)
    except Wordbook.DoesNotExist:
        return Response({
            'error': '해당 wordbook을 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # 데이터 검증
    serializer = ReviewSubmissionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'error': '잘못된 데이터 형식입니다.',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # wordbook_id 검증
    if data['wordbook_id'] != wordbook_id:
        return Response({
            'error': 'URL의 wordbook_id와 요청 데이터의 wordbook_id가 일치하지 않습니다.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 리뷰 결과 처리
    updated_words = []
    failed_words = []
    
    from django.utils import timezone
    current_time = timezone.now()
    
    for result in data['results']:
        word_id = result['word_id']
        is_known = result['is_known']
        
        try:
            sentence_word = SentenceWord.objects.get(
                id=word_id,
                sentence__wordbook=wordbook,
                word__user=user
            )
            
            # 단어의 복습 정보 업데이트
            word = sentence_word.word
            word.review_count += 1
            word.is_last_review_successful = is_known  # is_known을 success로 사용
            word.last_reviewed_at = current_time
            word.save()
            
            updated_words.append({
                'word_id': word_id,
                'word': word.text,
                'review_count': word.review_count,
                'is_known': is_known
            })
            
        except SentenceWord.DoesNotExist:
            failed_words.append({
                'word_id': word_id,
                'error': '해당 단어를 찾을 수 없습니다.'
            })
    
    # 응답 데이터 구성
    response_data = {
        'message': f'{len(updated_words)}개의 단어 리뷰가 완료되었습니다.',
        'updated_words': updated_words,
        'total_updated': len(updated_words),
        'wordbook_id': wordbook_id
    }
    
    if failed_words:
        response_data['failed_words'] = failed_words
        response_data['total_failed'] = len(failed_words)
    
    return Response(response_data, status=status.HTTP_200_OK)
