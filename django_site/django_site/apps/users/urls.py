from django.urls import path, re_path

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers

from . import views

urlpatterns = [
    # 判断用户名是否注册
    re_path(r'usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view()),
    # 判断手机号是否注册
    re_path(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/', views.MobileCountView.as_view()),

    # 注册用户
    path('users/', views.UserView.as_view()),

    # JWT登陆
    # path('authorizations/', obtain_jwt_token),
    path('authorizations/', views.UserAuthorizerView.as_view()),

    # 获取用户详情
    path('user/', views.UserDetailView.as_view()),

    # 更新邮箱
    path('email/', views.EmailView.as_view()),
    # 邮箱激活
    path('emails/verification/', views.EmailVerifyView.as_view()),

    # 商品浏览记录
    path('browse_histories/', views.UserBrowserHistoryView.as_view()),
]

router = routers.DefaultRouter()
router.register('addresses', views.AddressViewSet, basename='addresses')
urlpatterns += router.urls
