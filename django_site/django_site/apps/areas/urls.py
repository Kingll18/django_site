from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    # 查询所有省
    # path('areas/', views.AreaListView.as_view()),
    # path('areas/<int:pk>/', views.AreaDetailView.as_view()),
]

router = DefaultRouter()
router.register('areas', views.AreaViewSet, basename='ares')
urlpatterns += router.urls
