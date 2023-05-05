from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.filters import OrderingFilter
from drf_haystack.viewsets import HaystackViewSet
from .serializers import SKUSerializer, SKUIndexSerializer
from .models import SKU


class SKUListView(ListAPIView):
    """商品列表查询"""
    serializer_class = SKUSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ('create_time', 'price', 'sales')

    # queryset = SKU.objects.filter(name="手机")

    # 重写
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(is_launched=True, category_id=category_id)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]
    serializer_class = SKUIndexSerializer
