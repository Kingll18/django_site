from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers
from .models import SKU
from .search_indexes import SKUIndex


class SKUSerializer(serializers.ModelSerializer):
    """sku商品序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']


class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    object = SKUSerializer(read_only=True)  # 只序列化

    class Meta:
        index_classes = [SKUIndex]  # 索引类的名称
        fields = ['text', 'object']  # text 由索引类进行返回， object 由序列化进行返回，第一个参数必须是text
