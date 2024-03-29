"""django_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path, include
import xadmin

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('xadmin/', xadmin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),  # 富文本编辑器

    path('', include('verifications.urls')),  # 验证码
    path('', include('users.urls')),  # 用户
    path('', include('areas.urls')),  # 省市区模块
    path('', include('goods.urls')),  # 商品模块
    path('', include('carts.urls')),  # 购物车模块
    path('', include('orders.urls')),  # 订单模块
    path('', include('payment.urls')),  # 支付模块
]
