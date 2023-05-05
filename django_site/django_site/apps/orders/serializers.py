from rest_framework import serializers
from goods.models import SKU, Goods
from .models import OrderInfo, OrderGoods
from django.utils.datetime_safe import datetime
from decimal import Decimal
from django_redis import get_redis_connection
from django.db import transaction


class CartSKUSerializer(serializers.ModelSerializer):
    """订单中商品的序列化"""
    count = serializers.IntegerField(label="商品的购买数量")

    class Meta:
        model = SKU
        fields = ['id', 'name', 'default_image_url', 'price', 'count']


class OrdersSettlementSerializer(serializers.Serializer):
    """订单结算数据序列化器"""
    skus = CartSKUSerializer(many=True)
    freight = serializers.DecimalField(label="运费", max_digits=10, decimal_places=2)


class CommitOrderSerializer(serializers.ModelSerializer):
    """保存订单  序列化器"""

    class Meta:
        model = OrderInfo
        fields = ['order_id', 'address', 'pay_method']
        read_only_fields = ['order_id']  # 只会序列化
        extra_kwargs = {  # 这两个字段只会进行反序列化
            'address': {'write_only': True},
            'pay_method': {'write_only': True},
        }

    def create(self, validated_data):
        """在这里 我们同时操作了四张表 订单基本信息表, sku表, spu表, 订单中商品表  四张表要么一起成功，要么都不修改"""
        """保存订单 创建订单"""
        # 获取用户对象
        user = self.context['request'].user
        # 订单编号  拿当前时间+用户id  20230105153819000000002
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        # 获取前端传入的收货地址
        address = validated_data.get('address')
        # 获取前端传入的支付方式
        pay_method = validated_data.get('pay_method')
        # 订单状态 (1, "待支付") (2, "待发货") (3, "待收货") (4, "待评价") (5, "已完成") (6, "已取消")
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        with transaction.atomic():  # 手动开启事务
            # 创建事务保存点
            save_point = transaction.savepoint()
            try:
                # 保存订单数据  OrderInfo
                orderInfo = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,  # 订单中商品总数量
                    total_amount=Decimal('0.00'),  # 订单总金额
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status,
                )
                # 从redis读取购物车中被选中的商品信息
                # 创建redis连接对象
                redis_conn = get_redis_connection('cart')
                # 把redis中hash和set的购物车数据全部获取出来  {sku_id_1: 2}
                cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)
                selected_ids = redis_conn.smembers('selected_%d' % user.id)

                # 遍历购物车中选中的商品
                for sku_id_bytes in selected_ids:
                    while True:
                        # 获取SKU对象
                        sku = SKU.objects.get(id=sku_id_bytes)

                        # 获取当前商品的购买数量
                        buy_count = int(cart_dict_redis[sku_id_bytes])
                        # 把当前sku模型中的库存和销量都分别先获取出来
                        origin_sales = sku.sales  # 获取当前要购买商品的原有销量
                        origin_stock = sku.stock  # 获取当前要购买商品的原有库存

                        # 判断库存
                        if buy_count > origin_stock:  # 如果购买的数量大于了库存
                            raise serializers.ValidationError('库存不足')

                        # 减少库存，增加销量 SKU
                        # 计算新的库存和销量
                        new_sales = origin_sales + buy_count
                        new_stock = origin_stock - buy_count

                        # sku.sales = new_sales  # 修改sku模型的销量
                        # sku.stock = new_stock  # 修改sku模型的库存
                        # sku.save()
                        result = SKU.objects.filter(id=sku.id, stock=origin_stock).update(
                            sales=new_sales,
                            stock=new_stock,
                        )
                        if result == 0:  # 0就是没有修改成功， 说明抢夺了
                            continue
                        # 修改SPU
                        spu = sku.goods
                        old_spu_sales = spu.sales
                        res = Goods.objects.filter(id=spu.id, sales=old_spu_sales).update(
                            sales=old_spu_sales + buy_count
                        )
                        if res == 0:  # 0就是没有修改成功， 说明抢夺了
                            continue

                        # 保存订单商品信息 OrderGoods
                        OrderGoods.objects.create(
                            order=orderInfo,
                            sku=sku,
                            count=buy_count,
                            price=sku.price
                        )

                        orderInfo.total_count += buy_count
                        orderInfo.total_amount += (sku.price * buy_count)
                        break  # 当前这个商品下单成功，跳出循环，进行对下一个商品下单
                # 最后加入运费和保存订单
                orderInfo.total_amount += orderInfo.freight
                orderInfo.save()

            except:
                # 进行暴力回滚
                transaction.savepoint_rollback(save_point)
                raise serializers.ValidationError("库存不足")
            else:  # 不报错执行
                # 提交从保存点到当前状态的所有数据库事务操作
                transaction.savepoint_commit(save_point)  # 提交事务

        # 清除购物车中已结算的商品
        pl = redis_conn.pipeline()
        pl.hdel('cart_%d' % user.id, *selected_ids)  # hdel 删除一个或多个
        pl.srem('selected_%d' % user.id, *selected_ids)
        pl.execute()  # 执行

        # 返回订单模型
        return orderInfo
