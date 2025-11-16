from rest_framework import serializers

class ContentProcessingSerializer(serializers.Serializer):
    """
    이미지, 텍스트, 유튜브 링크 중 하나를 입력받는 Serializer
    """
    image = serializers.ImageField(required=False)
    text = serializers.CharField(required=False)
    youtube_link = serializers.URLField(required=False)

    def validate(self, data):
        if len([val for val in data.values() if val]) != 1:
            raise serializers.ValidationError("Provide exactly one of: image, text, or youtube_link.")
        return data

class GPTSentenceAnalyzeSerializer(serializers.Serializer):
    """
    문장 리스트를 GPT를 이용해 분석하고,
    각 문장의 번역과 주요 단어 정보를 반환하는 Serializer
    """
    sentences = serializers.ListField(child=serializers.CharField()) 
    language = serializers.CharField(required=False, default='english')