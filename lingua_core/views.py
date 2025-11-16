from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
import logging
import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from lingua_core.serializers.extraction_serializers import GPTSentenceAnalyzeSerializer
from lingua_core.utils.call_gpt_for_sentence import call_gpt_for_sentence
# from lingua_core.services import extract_words_with_boxes, extract_sentences_from_image, split_sentences

logger = logging.getLogger('lingua_core')



# class OcrView(APIView):
#     """
#     이미지(OCR), 텍스트, 유튜브 링크 등 다양한 출처에서 텍스트를 추출하고 단어 단위로 반환합니다. 
#     """
#     permission_classes = [AllowAny] # 테스트를 위해 임시 변경
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         manual_parameters=[
#             openapi.Parameter(
#                 'image',
#                 openapi.IN_FORM,
#                 description="분석할 이미지 파일",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             )
#         ],
#         operation_summary="OCR을 통해 이미지에서 단어/문장 추출",
#         consumes=['multipart/form-data']
#     )
#     def post(self, request):
#         if 'image' not in request.FILES:
#             return Response({'error': '이미지 파일이 필요합니다.'}, status=400)
        
#         image = request.FILES['image']
#         # image_processing 서비스 레이어를 통해 처리 (미구현)
#         words = extract_words_with_boxes(image)
#         response_data = {"words": words}
#         return Response(response_data)

# class OcrSentenceView(APIView):
#     """
#     이미지(OCR), 텍스트, 유튜브 링크 등 다양한 출처에서 텍스트를 추출하고 문장 단위로 반환합니다. 
#     """
#     permission_classes = [AllowAny] # 테스트를 위해 임시 변경
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(
#         manual_parameters=[
#             openapi.Parameter(
#                 'image',
#                 openapi.IN_FORM,
#                 description="분석할 이미지 파일",
#                 type=openapi.TYPE_FILE,
#                 required=True
#             )
#         ],
#         operation_summary="OCR을 통해 이미지에서 단어/문장 추출",
#         consumes=['multipart/form-data']
#     )
#     def post(self, request):
#         if 'image' not in request.FILES:
#             return Response({'error': '이미지 파일이 필요합니다.'}, status=400)
        
#         image = request.FILES['image']
#         # image_processing 서비스 레이어를 통해 처리 (미구현)
#         sentences = extract_sentences_from_image(image)
#         response_data = {"sentences": sentences}
#         return Response(response_data)

# class SentenceSplitView(APIView):
#     """
#     입력된 문장을 분할하여 반환합니다.
#     """
#     permission_classes = [AllowAny]
#     parser_classes = [FormParser]
    
#     @swagger_auto_schema(
#         manual_parameters=[
#             openapi.Parameter(
#                 'text',
#                 openapi.IN_FORM,
#                 description="분석할 텍스트",
#                 type=openapi.TYPE_STRING,
#                 required=True
#             )
#         ],
#         operation_summary="문장 분할"
#     )
#     def post(self, request):
#         text = request.data.get('text')
#         sentences = split_sentences(text)
#         return Response({"sentences": sentences})


class SentenceAnalyzeView(APIView):
    """
    입력된 문장 리스트를 GPT를 이용해 분석하고,
    각 문장의 번역과 주요 단어 정보를 반환합니다.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=GPTSentenceAnalyzeSerializer,
        operation_summary="문장 리스트를 AI로 분석"
    )
    def post(self, request):
        logger.info(f"Raw request data: {request.data}")
        logger.info(f"Request data type: {type(request.data)}")
        
        serializer = GPTSentenceAnalyzeSerializer(data=request.data)
        
        # Validation 상세 로깅
        if not serializer.is_valid():
            logger.error(f"Serializer validation failed: {serializer.errors}")
            return Response({'error': serializer.errors}, status=400)
        
        logger.info(f"Serializer validation successful")
        logger.info(f"Validated data: {serializer.validated_data}")
        
        sentences = serializer.validated_data.get('sentences', [])
        logger.info(f"받은 문장: {sentences}")
        language = serializer.validated_data.get('language', 'english')
        logger.info(f"받은 언어: {language}")
        logger.info(f"받은 문장 개수: {len(sentences)}")
        logger.info(f"받은 문장들: {sentences}")
        
        result = []
        for i, sent in enumerate(sentences):
            logger.info(f"처리 중인 문장 {i+1}: {sent}")
            gpt_response = call_gpt_for_sentence(sent, language)
            logger.info(f"GPT 응답 {i+1}: {gpt_response}")
            if gpt_response:
                result.append(gpt_response)
            else:
                logger.warning(f"문장 {i+1}에 대한 GPT 응답이 없음")
        
        logger.info(f"최종 결과 개수: {len(result)}")
        return Response({"selected": result})


# @method_decorator(csrf_exempt, name='dispatch')
# class GPTSentenceAnalyzeStreamView(APIView):
    # """
    # 문장 리스트를 AI로 분석하고 처리 완료되는 대로 실시간 스트리밍으로 반환
    # """
    # permission_classes = [AllowAny]

    # @swagger_auto_schema(
    #     request_body=GPTSentenceAnalyzeSerializer,
    #     operation_summary="문장 리스트를 AI로 분석 (실시간 스트리밍)"
    # )
    # def post(self, request):
    #     serializer = GPTSentenceAnalyzeSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
        
    #     sentences = serializer.validated_data.get('sentences', [])
    #     logger.info(f"스트리밍 - 받은 문장 개수: {len(sentences)}")
        
    #     def event_stream():
    #         """SSE 이벤트 스트림 생성기"""
    #         try:
    #             # 시작 이벤트
    #             yield f"data: {json.dumps({'type': 'start', 'total': len(sentences)})}\n\n"
                
    #             for i, sent in enumerate(sentences):
    #                 logger.info(f"스트리밍 - 처리 중인 문장 {i+1}: {sent}")
                    
    #                 # 처리 시작 이벤트
    #                 yield f"data: {json.dumps({'type': 'processing', 'index': i, 'sentence': sent})}\n\n"
                    
    #                 gpt_response = call_gpt_for_sentence(sent)
                    
    #                 if gpt_response:
    #                     # 성공 이벤트
    #                     yield f"data: {json.dumps({'type': 'result', 'index': i, 'data': gpt_response})}\n\n"
    #                     logger.info(f"스트리밍 - 문장 {i+1} 완료")
    #                 else:
    #                     # 실패 이벤트
    #                     yield f"data: {json.dumps({'type': 'error', 'index': i, 'message': 'GPT 응답 실패'})}\n\n"
    #                     logger.warning(f"스트리밍 - 문장 {i+1} 실패")
                
    #             # 완료 이벤트
    #             yield f"data: {json.dumps({'type': 'complete'})}\n\n"
    #             logger.info("스트리밍 완료")
                
    #         except Exception as e:
    #             logger.error(f"스트리밍 오류: {e}")
    #             yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
    #     response = StreamingHttpResponse(
    #         event_stream(),
    #         content_type='text/event-stream'
    #     )
    #     response['Cache-Control'] = 'no-cache'
    #     response['Connection'] = 'keep-alive'
    #     response['Access-Control-Allow-Origin'] = '*'
    #     response['Access-Control-Allow-Headers'] = 'Content-Type'
        
    #     return response 
