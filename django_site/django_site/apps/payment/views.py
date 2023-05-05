from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from orders.models import OrderInfo
from alipay import AliPay
import os
from django.conf import settings
from .models import Payment


class PaymentView(APIView):
    """生成支付链接"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        # 校验订单的有效性
        try:
            order_model = OrderInfo.objects.get(
                order_id=order_id, user=user,
                pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY'],
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({"message": "订单有误"}, status.HTTP_400_BAD_REQUEST)

        # 创建AliPay  SDK中提供的支付对象
        app_private_key_string = open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem')
        ).read()
        alipay_public_key_string = open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")
        ).read()
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_private_key_string=app_private_key_string,  # 自己的私钥
            alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥
            sign_type="RSA2",  # 加密方式
            debug=settings.ALIPAY_DEBUG,
            app_notify_url=None,  # 默认回调的URL
        )
        # 调用SDK的方法得到支付链接后面的查询参数
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order_model.total_amount),  # 支付总金额  它不认识Decimal
            subject="荣芊商城 ---- %s" % order_id,
            return_url='http://127.0.0.1:8080/pay_success.html',
            notify_url=" "  # 异步回调地址   就算不用也要加上
        )
        print(order_string)
        # 拼接好支付链接
        alipay_url = settings.ALIPAY_URL + "?" + order_string

        # 响应
        return Response({"alipay_url": alipay_url})


class PaymentStatusView(APIView):

    def put(self, request):
        # 获取前端以查询字符串方式传入的数据
        queryDict = request.query_params
        # 将queryDict类型转换成字典（要将中间的sign 从里面移除，然后进行验证）
        data = queryDict.dict()
        # 将sign这个数据从字典中移除 pop
        sign = data.pop('sign')

        # 创建AliPay  SDK中提供的支付对象
        app_private_key_string = open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem')
        ).read()
        alipay_public_key_string = open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem")
        ).read()
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_private_key_string=app_private_key_string,  # 自己的私钥
            alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥
            sign_type="RSA2",  # 加密方式
            debug=settings.ALIPAY_DEBUG,
            app_notify_url=None,  # 默认回调的URL
        )
        if alipay.verify(data, sign):
            """校验成功"""
            order_id = data.get("out_trade_no")  # 荣芊订单编号
            trade_no = data.get("trade_no")  # 支付宝流水号
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_no,
            )
            try:
                new_orderinto = OrderInfo.objects.get(
                    order_id=order_id,
                    user=request.user,
                    pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY'],
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                new_orderinto.status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                new_orderinto.save()
                # 完成
                return Response({"trade_id": trade_no})
            except OrderInfo.DoesNotExist:
                return Response({"message": "订单有误"}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "非法请求"}, status=status.HTTP_403_FORBIDDEN)
