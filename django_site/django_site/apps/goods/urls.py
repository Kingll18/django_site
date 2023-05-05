from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    # 商品列表数据
    re_path('categories/(?P<category_id>\d+)/skus/', views.SKUListView.as_view()),
]

router = DefaultRouter()
"""为了搜索"""
router.register('skus/search', views.SKUSearchViewSet, basename='skus_search')
urlpatterns += router.urls
