from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import AreasSerializer, SubsSerializer
from .models import Area


# class AreaListView(GenericAPIView):
#     """查询所有省"""
#     serializer_class = AreasSerializer
#     queryset = Area.objects.filter(parent=None)
#
#     def get(self, request):
#         qs = self.get_queryset()
#         serializer = self.get_serializer(instance=qs, many=True)
#         return Response(serializer.data)

# class AreaDetailView(GenericAPIView):
#     serializer_class = SubsSerializer
#     queryset = Area.objects.all()
#
#     def get(self, request, pk):
#         area = self.get_object()
#         serializer = self.get_serializer(instance=area)
#         return Response(serializer.data)

# ---------------------------------------------------------------------

# class AreaListView(ListAPIView):
#     """查询所有省"""
#     serializer_class = AreasSerializer
#     queryset = Area.objects.filter(parent=None)
#
#
# class AreaDetailView(RetrieveAPIView):
#     serializer_class = SubsSerializer
#     queryset = Area.objects.all()

# ---------------------------------------------------------------------

# CacheResponseMixin 缓存技术 需要在setting进行配置
class AreaViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    pagination_class = None  # 禁用分页

    # 指定查询集
    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """重写这个方法  因为我们有两个序列化器  不好区分"""
        # self.action 可以知道当前的请求 是那一个方法的 那一个动作
        if self.action == 'list':
            return AreasSerializer
        else:
            return SubsSerializer


'''
列表
    get  --》List
    
详情视图
    get --》Retrieve
'''
