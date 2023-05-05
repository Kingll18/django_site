from django.shortcuts import render
from django_redis import get_redis_connection
from random import randint
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('django')


class SMSCodeView(APIView):
    """短信验证码"""

    def get(self, request, mobile):
        """
        @param mobile:  手机号
        """
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')  # verify_codes 是配置里面的CACHES字段
        # 先从redis获取发送的标记
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 如果取到了标记，说明此手机号频繁发短信
        if send_flag:
            return Response({'message': '手机频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        # 创建redis管道：（把多次redis操作装入管道中，将来一次性去执行，减少redis的连接操作）
        pl = redis_conn.pipeline()
        # 把验证码存储到redis数据库
        # redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        pl.setex('sms_%s' % mobile, 300, sms_code)
        # 存储一个标记，表示手机号已发送过短信 标记有效期60s
        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        pl.setex('send_flag_%s' % mobile, 60, 1)
        # 执行管道
        pl.execute()

        # 响应
        return Response({'message': 'ok'})


"""
register.html:1 Access to XMLHttpRequest at 'http://127.0.0.1:8000/sms_codes/18273390853/' from origin 'http://127.0.0.1:8080' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.

跨域问题  CORS
浏览器  同源策略
ip/域名  端口
127.0.0.1:8000/login
127.0.0.1:8000/index

127.0.0.1:8080/count/

"""


