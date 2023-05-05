from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData

from django.conf import settings
from django_redis import get_redis_connection
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_jwt.settings import api_settings
from datetime import datetime

from carts.utils import merge_cart_cookie_to_redis
from .models import User, Address
from goods.models import SKU
from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer, \
    AddressTitleSerializer, UserBrowserHistorySerializer, SKUSerializer


class UsernameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        获取指定用户名数量
        """
        # User.objects.filter(username=username)  # 判断查询集是不是空的
        # User.objects.get(username=username) # 瞅瞅会不会报错
        count = User.objects.filter(username=username).count()
        data = {
            "username": username,
            "count": count
        }
        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()
        data = {
            "mobile": mobile,
            "count": count
        }
        return Response(data)


# class UserView(GenericAPIView):
#     """用户注册"""
#     # 指定序列化器
#     serializer_class = CreateUserSerializer
#
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)  # 校验  raise_exception=True直接进行“报错”  这个"报错"将会被我自动捕捉异常
#         serializer.save()
#
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserView(CreateAPIView):
    """用户注册"""
    # 指定序列化器
    serializer_class = CreateUserSerializer


# GET /user/
# class UserDetailView(GenericAPIView):
#     """用户详细信息展示"""
#     serializer_class = UserDetailSerializer
#
#     def get(self, request):
#         # print(request.user)  # 如果没登录  那就是匿名用户   anonymous
#         # print(type(request.user))
#
#         serializer = self.get_serializer(instance=request.user)
#         return Response(serializer.data)


# GET /user/
class UserDetailView(RetrieveAPIView):
    """用户详细信息展示"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]  # 指定权限 只有用过认证的用户才能看到当前视图

    # queryset = User.objects.all()

    def get_object(self):
        """重写此方法返回， 要展示的用户模型对象"""
        return self.request.user


# PUT /email/
class EmailView(GenericAPIView):
    """修改更新用户邮箱"""
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        instance = request.user
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# GET /email/verification/?token=xxx
class EmailVerifyView(APIView):
    """激活用户邮箱"""

    def get(self, request):
        # 获取前端查询字符串中传入的token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)
        # 吧token进行解密  并查询对应的user
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message': '激活失败'}, status=status.HTTP_400_BAD_REQUEST)

        # 数据库操作
        user.email_active = True
        user.save()

        # 响应
        return Response({'message': 'ok'})


class AddressViewSet(GenericViewSet):
    """用户收货地址  增删改查"""
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    # queryset = Address.objects.filter(is_deleted=False)

    # 重写
    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # POST /addresses/
    def create(self, request):
        """
        创建收货地址
        """
        user = request.user
        # count = Address.objects.filter(user=user).count()
        count = user.addresses.all().count()
        # 用户收货有上限，最多只能有20个
        if count >= 20:
            return Response({'message': '收货地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)

        # print(request.data)
        '''
        前端传来的
            'receiver': 'bailu', 
            'province_id': 140000, 
            'city_id': 140500, 
            'district_id': 140525,
            'place': 'xxxxxxxxxxxxxxxxxxxxxx', 
            'mobile': '18212345678', 
            'tel': '', 
            'email': '',
            'title': 'bailu'
            {"province":["该字段是必填项。"],"city":["该字段是必填项。"],"district":["该字段是必填项。"]}
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        '''
        响应回去的数据
            city: "晋城市"
            city_id: 140500
            district: "泽州县"
            district_id: 140525
            email: ""
            id: 1
            mobile: "18212345678"
            place: "xxxxxxxxxxxxxxxxxxxxxx"
            province: "山西省"
            province_id: 140000
            receiver: "bailu"
            tel: ""
            title: "bailu"
        '''
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /addresses/
    def list(self, request):
        """
        用户地址列表数据
        """
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data
        })

    # delete /addresses/<pk>/
    def destroy(self, request, pk):
        """
        处理删除
        """
        # address = Address.objects.get(id=pk)
        address = self.get_object()
        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/<pk>/
    def update(self, request, pk):
        """
        更新数据
        """
        address = self.get_object()
        serializer = self.get_serializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # put /addresses/pk/title/  # 路由中的title 其实就是对应下面的 def title()方法
    @action(methods=['put'], detail=True)
    def title(self, request, pk):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    """
    @action()
    action装饰器可以接受两个参数：
        methods：声明该action对应的请求方式
        detail：声明该action的路径是否与单一资源对应  
            True  格式是  xxxx/<pk>/action方法名
            False  格式是  xxxx/action方法名
    """

    @action(methods=['put'], detail=True)
    def status(self, request, pk):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


class UserBrowserHistoryView(CreateAPIView):
    """用户商品浏览记录"""
    serializer_class = UserBrowserHistorySerializer
    permission_classes = [IsAuthenticated]  # 指定权限  登陆用户

    def get(self, request):
        """查询商品浏览记录"""
        # 获取当前请求的用户
        user = request.user
        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        # 获取redis中当前用户的浏览记录列表数据
        sku_ids = redis_conn.lrange('history_%d' % user.id, 0, -1)

        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)
        # 创建序列化器进行序列化
        serializer = SKUSerializer(sku_list, many=True)
        # 响应
        return Response(serializer.data)


jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


class UserAuthorizerView(ObtainJSONWebToken):
    """自定义账号密码登录视图吗，实现购物车登录合并"""

    # 写法一
    # 此处的post方法是重写方法
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():  # 判断账号密码
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            # 账号登陆时合并购物车数据
            merge_cart_cookie_to_redis(request, user, response)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 写法二
    '''
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # 合并购物车
        response = merge_cart_cookie_to_redis(request, request.user, response)

        return response
    '''
