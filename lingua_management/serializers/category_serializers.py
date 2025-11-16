from rest_framework import serializers

from lingua_management.models import Category

class CategorySerializer(serializers.ModelSerializer):
    """
    카테고리 목록을 조회하는 Serializer
    """
    class Meta:
        model = Category
        fields = ['id', 'name']

class CategoryRelatedField(serializers.PrimaryKeyRelatedField):
    """
    카테고리 ID(int) 또는 이름(str)을 받아 처리하는 커스텀 필드.
    이름으로 된 카테고리가 없으면 새로 생성합니다.
    """
    def to_internal_value(self, data):
        if isinstance(data, str):
            # 문자열로 카테고리 이름이 들어온 경우
            user = self.context['request'].user
            category, _ = Category.objects.get_or_create(user=user, name=data)
            return category
        # 기본 동작 (ID로 처리)
        return super().to_internal_value(data)
