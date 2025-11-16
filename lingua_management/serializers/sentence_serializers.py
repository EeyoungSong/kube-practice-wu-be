from rest_framework import serializers

from lingua_management.models import SentenceWord, Sentence

class SentenceWordSerializer(serializers.ModelSerializer):
    """
    Sentence 내에서 단어의 문맥별 뜻을 보여주기 위한 Serializer
    """
    id = serializers.ReadOnlyField(source='word.id')
    text = serializers.ReadOnlyField(source='word.text')
    others = serializers.ReadOnlyField(source='word.others')


    class Meta:
        model = SentenceWord
        fields = ['id', 'text', 'meaning', 'others', 'pos', 'memo']

class SentenceSerializer(serializers.ModelSerializer):
    words = SentenceWordSerializer(many=True, source='word_links', read_only=True)

    class Meta:
        model = Sentence
        fields = [
            'id', 'text', 'meaning', 'words', 'last_reviewed_at', 
            'review_count', 'is_last_review_successful'
        ]
