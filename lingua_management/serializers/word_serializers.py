from rest_framework import serializers

from lingua_management.models import SentenceWord, Word
from lingua_management.serializers.sentence_serializers import SentenceSerializer

class WordExampleSerializer(serializers.Serializer):
    sentence = SentenceSerializer(read_only=True)
    meaning = serializers.CharField(help_text="해당 문장에서의 단어의 뜻")

    class Meta:
        model = SentenceWord
        fields = ['sentence', 'meaning'] 


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = [
            'id', 'text', 'others', 'last_reviewed_at', 
            'review_count', 'is_last_review_successful'
        ]

class WordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['text']


# 기존 단일 의미 구조용 (wordbook_id 기반)
class ReviewWordLegacySerializer(serializers.Serializer):
    """리뷰용 단어 데이터 직렬화 (단일 의미)"""
    id = serializers.CharField()
    word = serializers.CharField()
    meaning = serializers.CharField()
    others = serializers.CharField()
    pos = serializers.CharField()
    context = serializers.CharField()


# 새로운 다중 의미 구조용 (category 기반)
class ReviewWordMeaningSerializer(serializers.Serializer):
    """리뷰용 단어의 개별 의미 데이터 직렬화"""
    id = serializers.CharField()
    meaning = serializers.CharField()
    others = serializers.CharField()
    pos = serializers.CharField()
    context = serializers.CharField()


class ReviewWordMultiMeaningSerializer(serializers.Serializer):
    """리뷰용 단어 데이터 직렬화 (다중 의미 지원)"""
    word = serializers.CharField()
    meanings = ReviewWordMeaningSerializer(many=True)


# 유연한 리뷰 데이터 시리얼라이저
class ReviewDataSerializer(serializers.Serializer):
    """리뷰 데이터 직렬화 (단일/다중 의미 구조 모두 지원)"""
    words = serializers.ListField()  # 유연한 구조 허용
    total_count = serializers.IntegerField()
    
    def to_representation(self, instance):
        """데이터 구조에 따라 적절한 시리얼라이저 선택"""
        data = super().to_representation(instance)
        
        # words 데이터가 비어있지 않고 첫 번째 항목을 확인
        if data['words'] and len(data['words']) > 0:
            first_word = data['words'][0]
            
            # 다중 의미 구조인지 확인 (meanings 키가 있는지)
            if isinstance(first_word, dict) and 'meanings' in first_word:
                # 다중 의미 구조 - 그대로 반환
                return data
            elif isinstance(first_word, dict) and 'id' in first_word:
                # 단일 의미 구조 - 그대로 반환  
                return data
        
        return data


class ReviewResultSerializer(serializers.Serializer):
    """리뷰 결과 직렬화"""
    word_id = serializers.CharField()
    is_known = serializers.BooleanField()


class ReviewSubmissionSerializer(serializers.Serializer):
    """리뷰 제출 데이터 직렬화"""
    wordbook_id = serializers.IntegerField()
    results = ReviewResultSerializer(many=True)
