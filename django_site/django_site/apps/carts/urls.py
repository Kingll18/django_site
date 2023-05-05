from django.urls import path

from . import views

urlpatterns = [
    # 购物车  增删改查
    path('carts/', views.CartView.as_view()),
]
