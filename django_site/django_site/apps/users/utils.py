def jwt_response_payload_handler(token, user=None, request=None):
    """重写JWT登陆视图的构造响应数据函数  多追加 user_id  username"""
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


from django.contrib.auth.backends import ModelBackend
import re
from .models import User


def get_user_by_account(account):
    """
    通过传入的账号动态识别是username还是mobil
    """
    try:
        if re.match(r'1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:  # 如果没有报错 返回user用户模型对象
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """修改django认证类  为了实现多账号登陆"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 获取到user
        user = get_user_by_account(username)
        # 判断当前前端传入的密码是否正确
        if user and user.check_password(password):
            return user
