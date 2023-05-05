from django.urls import path, re_path

from . import views

urlpatterns = [
    # 获取支付宝支付的URL
    re_path('^orders/(?P<order_id>\d+)/payment/$',views.PaymentView.as_view()),

    # 支付后验证状态
    path('payment/status/', views.PaymentStatusView.as_view()),
]
