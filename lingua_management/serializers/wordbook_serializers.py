from rest_framework import serializers

from lingua_management.models import Wordbook, Category, Word, SentenceWord
from lingua_management.serializers.category_serializers import CategoryRelatedField
from lingua_management.serializers.sentence_serializers import SentenceSerializer

class WordWithSentencesSerializer(serializers.ModelSerializer):
    """
    단어와 그 단어가 포함된 모든 문장들을 보여주는 Serializer
    """
    sentences = serializers.SerializerMethodField()
    
    class Meta:
        model = Word
        fields = ['id', 'text', 'others', 'sentences']
    
    def get_sentences(self, obj):
        # 현재 단어장 context 가져오기
        current_wordbook = self.context.get('wordbook')
        if not current_wordbook:
            return []
        
        # 해당 단어가 사용된 모든 문장들 가져오기 (모든 단어장에서)
        sentence_words = SentenceWord.objects.filter(
            word=obj,
            sentence__user=current_wordbook.user  # 같은 사용자의 문장들만
        ).select_related('sentence', 'sentence__wordbook')
        
        sentences_data = []
        for sw in sentence_words:
            sentence_data = SentenceSerializer(sw.sentence).data
            # 해당 문장에서 이 단어의 의미 추가
            sentence_data['word_meaning_in_context'] = sw.meaning
            sentence_data['word_pos_in_context'] = sw.pos
            sentence_data['word_memo_in_context'] = sw.memo
            # 현재 단어장에 속하는지 여부 표시
            sentence_data['is_current_wordbook'] = sw.sentence.wordbook.id == current_wordbook.id
            # 문장이 속한 단어장 정보 추가
            sentence_data['wordbook_info'] = {
                'id': sw.sentence.wordbook.id,
                'name': sw.sentence.wordbook.name,
                'category_name': sw.sentence.wordbook.category.name if sw.sentence.wordbook.category else None
            }
            sentences_data.append(sentence_data)
        
        # 현재 단어장 문장들을 먼저 정렬하고, 그 다음에 다른 단어장 문장들 정렬
        sentences_data.sort(key=lambda x: (not x['is_current_wordbook'], x['wordbook_info']['name']))
        
        return sentences_data

class WordbookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True) # 클라이언트 카테고리 이름 조회용 
    sentences = SentenceSerializer(many=True, read_only=True)
    words_with_sentences = serializers.SerializerMethodField()
    
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True # 클라이언트 카테고리 등록, 수정용
    )

    class Meta:
        model = Wordbook
        fields = [
            'id', 'name', 'category', 'category_name', 'language', 
            'input_type', 'created_at', 'sentences', 'words_with_sentences'
        ]
        read_only_fields = ['created_at', 'sentences', 'words_with_sentences']
    
    def get_words_with_sentences(self, obj):
        """
        해당 단어장에 포함된 모든 단어들과 각 단어가 연결된 문장들을 반환
        """
        # 단어장의 모든 문장에서 사용된 단어들을 중복 제거하여 수집
        words = Word.objects.filter(
            sentence_links__sentence__wordbook=obj
        ).distinct().order_by('text')
        
        # WordWithSentencesSerializer에 wordbook context 전달
        serializer = WordWithSentencesSerializer(
            words, 
            many=True, 
            context={'wordbook': obj}
        )
        return serializer.data

class WordbookUpdateSerializer(serializers.ModelSerializer):
    """
    단어장(노트)의 이름과 카테고리만 수정을 위한 Serializer
    """
    category = CategoryRelatedField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Wordbook
        fields = ['name', 'category']

## 단어장 생성 시 클라이언트가 보내는 데이터 형식 검증 & 직렬화

# 단어 
class WordSelectionSerializer(serializers.Serializer):
    text = serializers.CharField()
    meaning = serializers.CharField(required=False, allow_blank=True)
    others = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    pos = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    memo = serializers.CharField(required=False, allow_blank=True, allow_null=True)

# 문장 
class SentenceSelectionSerializer(serializers.Serializer):
    text = serializers.CharField()
    meaning = serializers.CharField(required=False, allow_blank=True)
    words = WordSelectionSerializer(many=True)

# 단어장 
class CommitSelectionSerializer(serializers.Serializer):
    category = serializers.CharField()
    name = serializers.CharField()
    language = serializers.CharField()
    input_type = serializers.CharField()
    sentences = SentenceSelectionSerializer(many=True) 

# 카테고리 형식 검증 & 직렬화
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# class WordbookDetailSerializer(serializers.ModelSerializer):
#     category = CategorySerializer(read_only=True)
#     sentences = SentenceSerializer(many=True, read_only=True)
    
#     class Meta:
#         model = Wordbook
#         fields = ['id', 'name', 'category', 'language', 'input_type', 'created_at', 'sentences']
