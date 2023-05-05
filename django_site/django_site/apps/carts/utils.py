import pickle
import base64
from django_redis import get_redis_connection

"""
登录时购物车数据合并是以cookie合并到redis，并清除cookie中的购物车数据。
对于cookie中的购物车商品如果和redis中有相同的 数量用cookie的覆盖redis
如果商品在cookie或redis中只要有一方是勾选的 那么最终它就是勾选的
"""


def merge_cart_cookie_to_redis(request, user, response):
    """登陆时合并购物车"""
    cart_str = request.COOKIES.get('cart')
    if cart_str is None:
        # 如果cookie中没有购物车数据  直接退出
        return
    # 解密
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    # 创建redis连接对象
    redis_conn = get_redis_connection('cart')
    pl = redis_conn.pipeline()

    for sku_id in cart_dict:
        # 把cookie中的sku_id和count先redid的hash去存储，如果存储的sku_id存在，就直接覆盖，不存在就新增
        pl.hset('cart_%d' % user.id, sku_id, cart_dict[sku_id]['count'])
        # 判断当前cookie中的商品是否勾选  如果勾选了 我才存
        if cart_dict[sku_id]['selected']:
            pl.sadd('selected_%d' % user.id, sku_id)
    pl.execute()  # 执行管道

    response.delete_cookie('cart')  # 删除cookie
    return response
