from django.urls import path
from . import views

urlpatterns = [
    # 去结算
    path('orders/settlement/', views.OrdersSettlementView.as_view()),

    # 保存订单
    path('orders/', views.CommitOrderView.as_view()),
]
