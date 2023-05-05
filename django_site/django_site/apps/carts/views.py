from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from .serializers import CartSerializer, SKUCartSerializer, CartDeletedSerializer

from django_redis import get_redis_connection
import base64
import pickle
from goods.models import SKU


class CartView(APIView):
    """购物车的增删改查"""""

    # 重写校验
    def perform_authentication(self, request):
        """重写父类的用户验证方法，不在进入视图前就检查JWT"""
        # 重写此方法 直接pass 可以延后认证 延后到第一次通过 request.user 或 request.auth才去做认证
        # 因为在前端中传入了 'Authorization': 'JWT ' + this.token  只要检测到请求头中有Authorization，就会去做用户认证。
        # 所以我们重写perform_authentication方法，为pass  就可以做到延后认证(暂时不进行JWT认证)
        pass

    def post(self, request):
        """增加 新增"""
        # 创建序列化器进行反序列化
        serializer = CartSerializer(data=request.data)
        # 调用is_valid进行校验
        serializer.is_valid(raise_exception=True)
        # 获取校验后的数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            # 执行此行代码时会执行认证逻辑，如果登陆用户认证会成功没有异常，但是未登陆用户认证会出异常我们自己捕获异常
            user = request.user
        except:
            user = None

        # is_authenticated  判断用户是不是匿名用户  是否通过认证  返回布尔类型
        if user and user.is_authenticated:  # 登陆用户
            """登陆用户操作redis购物车数据"""
            '''
            hash: {'sku_id_1': 2, 'sku_id_16': 2}  存储商品和数量
            set:{sku_id_1}  存储商品时候勾选
            '''
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()  # 创建管道
            # .hincrby() 如果要添加的sku_id在hash字典中不存在，就是新增，如果已存在，就会自动做增量计数再存储
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            # 把勾选的商品sku_id 存储到set集合中
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)

            pl.execute()  # 执行管道
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            """未登录用户操作cookie购物车数据"""
            '''格式
            cart : {
                'sku_id_1':{'count':1,'selected':True},
                'sku_id_26':{'count':1,'selected':True},
            }
            '''
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('cart')
            if cart_str:  # 说明cookie购物车有值，需要将值转换成字典
                # 把字符串转换成bytes类型的字符串
                cart__str_bytes = cart_str.encode()
                # 把bytes类型的字符串转换成bytes64类型
                cart_bytes = base64.b64decode(cart__str_bytes)
                # 把bytes类型转换成字典
                cart_dict = pickle.loads(cart_bytes)
            else:
                cart_dict = {}
            if sku_id in cart_dict:  # 判断当前要添加的sku-id在字典中是否已经存在
                origin_count = cart_dict[sku_id]['count']  # 原有的count
                count += origin_count  # 将原有的 和 本次的 进行累加
            # 把行的商品添加到cart_dict字典中
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 先将字段转换成bytes类型
            cart_bytes = pickle.dumps(cart_dict)
            # 在将bytes类型转换成bytes类型的字符串
            cart__str_bytes = base64.b64encode(cart_bytes)
            # 把bytes类型的字符串转换字符串
            cart_str = cart__str_bytes.decode()

            # 创建响应对象
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            response.set_cookie('cart', cart_str)
            return response

    def get(self, request):
        """查询"""
        try:
            user = request.user
        except:
            user = None
        if user and user.is_authenticated:
            """登陆用户获取redis数据"""
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            # 获取hash数据 {sku_id_1: 1, sku_id_16: 2}
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            # 获取set集合数据 {sku_id_1}
            selecteds = redis_conn.smembers('selected_%d' % user.id)
            # 将redis购物车数据格式转换成cookie购物车数据一致
            cart_dict = {}
            for sku_id_bytes, count_bytes in cart_redis_dict.items():  # 遍历hash中的所有键值对字典
                cart_dict[int(sku_id_bytes)] = {  # 包到字典的数据 注意类型转换
                    'count': int(count_bytes),
                    'selected': sku_id_bytes in selecteds
                }
        else:
            """未登录用户获取cookie购物车数据"""
            '''格式
            {
                'sku_id_1':{'count':1,'selected':True},
                'sku_id_26':{'count':1,'selected':True},
            }
            '''
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 解密
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据sku_id 查询sku模型
        sku_ids = cart_dict.keys()
        # __in 直接查询出符合条件的所有sku模型，返回查询集
        skus = SKU.objects.filter(id__in=sku_ids)
        # 给每个sku模型 多定义一个count和selected属性
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']  # 添加临时性的属性值
            sku.selected = cart_dict[sku.id]['selected']  # 添加临时性的属性值
        # 创建序列化器进行序列化
        serializer = SKUCartSerializer(skus, many=True)
        # 响应
        return Response(serializer.data)

    def put(self, request):
        """修改"""
        # 创建序列化器进行反序列化
        serializer = CartSerializer(data=request.data)
        # 调用is_valid进行校验
        serializer.is_valid(raise_exception=True)
        # 获取校验后的数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except:
            user = None
        if user and user.is_authenticated:
            """登陆用户修改redis购物车数据"""
            # 创建redis连接对象
            redis_conn = get_redis_connection("cart")
            # 创建管道
            pl = redis_conn.pipeline()
            # 覆盖sku_id 对应的count
            pl.hset('cart_%d' % user.id, sku_id, count)  # 将count直接覆盖
            # 如果勾选就把勾选的sku_id存储到set集合当中
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)  # 如果已存在  自动进行去重
            else:
                # 如果未勾选  就把商品的sku_id从set集合移除
                pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()  # 执行管道
            return Response(serializer.data)
        else:
            """未登录用户修改cookie购物车数据"""
            '''格式
            {
                'sku_id_1':{'count':1,'selected':True},
                'sku_id_26':{'count':1,'selected':True},
            }
            '''
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 解密
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)
            # 直接覆盖原cookie的数据
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected,
            }

            # 把cookies大字典在转换成字符串数据
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 设置cookie
            response = Response(serializer.data)
            response.set_cookie('cart', cart_str)
            return response

    def delete(self, request):
        """删除"""
        # 创建序列化器
        serializer = CartDeletedSerializer(data=request.data)
        # 校验
        serializer.is_valid(raise_exception=True)
        # 获取校验后的数据
        sku_id = serializer.validated_data.get('sku_id')

        try:
            user = request.user
        except:
            user = None
        if user and user.is_authenticated:
            """登陆用户操作redis数据"""
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 删除hash数据
            pl.hdel('cart_%d' % user.id, sku_id)
            # 删除set数据
            pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()  # 执行管道
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            """未登录用户操作cookie数据"""
            '''格式
                        {
                            'sku_id_1':{'count':1,'selected':True},
                            'sku_id_26':{'count':1,'selected':True},
                        }
                        '''
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 解密
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return Response({'message': '没有购物车数据'}, status=status.HTTP_400_BAD_REQUEST)
            # 把删除的sku_id 从cookie字典中移除
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            response = Response(serializer.data)
            if len(cart_dict.keys()):  # 如果cookie字典中还有商品
                # 把cookies大字典在转换成字符串数据
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置cookie
                response.set_cookie('cart', cart_str)
            else:
                # cookie购物车数据已经清空了，就直接删除购物车cookie
                response.delete_cookie("cart")  # 删除cookie
            return response
