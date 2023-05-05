from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(label="商品ID", min_value=1, required=True)
    count = serializers.IntegerField(label="购买数量", min_value=1)
    selected = serializers.BooleanField(label="时候勾选", default=True)

    def validate(self, attrs):
        """校验商品存不存在"""
        try:
            SKU.objects.get(id=attrs['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return attrs


class SKUCartSerializer(serializers.ModelSerializer):
    """购物车查询序列化器"""

    count = serializers.IntegerField(label='购买数量')
    selected = serializers.BooleanField(label='是否勾选')

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')


class CartDeletedSerializer(serializers.Serializer):
    """购物车删除序列化器"""
    sku_id = serializers.IntegerField(label="商品ID", min_value=1, required=True)

    def validate(self, attrs):
        """校验商品存不存在"""
        try:
            SKU.objects.get(id=attrs['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return attrs
