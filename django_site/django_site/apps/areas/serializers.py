from rest_framework import serializers
from .models import Area


class AreasSerializer(serializers.ModelSerializer):
    """省的序列化器"""

    class Meta:
        model = Area
        fields = ['id', 'name']


class SubsSerializer(serializers.ModelSerializer):
    """单一查询省或市"""

    subs = AreasSerializer(many=True)  # subs是在定义模型里面的  "related_name='subs'"  不能改变  实例.subs.all()

    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']
