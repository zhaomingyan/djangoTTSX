from django.shortcuts import render
from django.http import JsonResponse
from django.http import Http404
from tt_goods.models import GoodsSKU
import json
from django_redis import get_redis_connection


# Create your views here.

def add(request):
    if request.method != 'POST':
        return Http404

    dict = request.POST
    sku_id = dict.get('sku_id')
    count = int(dict.get('count', 0))

    # 验证数据有效性
    # 判断数据编号是否合法
    if GoodsSKU.objects.filter(id=sku_id).count() <= 0:
        return JsonResponse({'status': 2})
    # 判断数据数量是否合法
    if count <= 0:
        return JsonResponse({'status': 3})
    if count >= 5:
        count = 5

    if request.user.is_authenticated():
        # 如果已经登录，则购物车信息存储到redis中
        redis_client = get_redis_connection()
        key = 'cart%d' % request.user.id
        # 判断redis中商品是否已经存在
        if redis_client.hexists(key, sku_id):
            # 如果存在数量相加
            count1 = int(redis_client.hget(key, sku_id))
            count2 = count
            count0 = count1 + count2
            if count0 > 5:
                count0 = 5
            redis_client.hset(key, sku_id, count0)
        else:
            # 如果不存在则添加
            redis_client.hset(key, sku_id, count)
        total_count = 0
        for v in redis_client.hvals(key):
            total_count += int(v)
        # 构造返回结果
        response = JsonResponse({'status': 1, 'total_count': total_count})

    else:
        # 如果未登录，则购物车信息存储到cookie中
        cart_dict = {}
        # 先读出cookie中的数据
        cart_str = request.COOKIES.get('cart')
        if cart_str:
            cart_dict = json.loads(cart_str)
        # 将指定的商品加入购物车
        # 判断购物车中有没有该商品
        if sku_id in cart_dict:
            # 如果商品已存在
            count1 = cart_dict[sku_id]
            count0 = count1 + count
            if count0 > 5:
                count0 = 5
            cart_dict[sku_id] = count0

        else:
            # 如果商品不存在
            cart_dict[sku_id] = count

        # 计算商品总数量
        total_count = 0
        for k, v in cart_dict.items():
            total_count += v

        # 将字典转成字符串
        cart_str = json.dumps(cart_dict)

        response = JsonResponse({'status': 1, 'total_count': total_count})
        # 写入cookie
        response.set_cookie('cart', cart_str, expires=60 * 60 * 24 * 30)

    return response


def index(request):
    # 查询购物车中的商品信息
    sku_list = []
    if request.user.is_authenticated():
        # 如果登陆了从redis中读取
        redis_client = get_redis_connection()
        key = 'cart%d' % request.user.id
        id_list = redis_client.hkeys(key)
        for id1 in id_list:
            sku = GoodsSKU.objects.get(pk=id1)
            sku.cart_count = int(redis_client.hget(key, id1))
            sku_list.append(sku)

    else:
        # 如果没有登录从cookie中读取
        cart_str = request.COOKIES.get('cart')
        # 判断当前购物车是否有信息
        if cart_str:
            # 将购物车字符串转成字典
            cart_dict = json.loads((cart_str))
            # 遍历字典，根据商品编号查询商品对象
            for k, v in cart_dict.items():
                sku = GoodsSKU.objects.get(pk=k)
                sku.cart_count = v
                sku_list.append(sku)

    context = {
        'sku_list': sku_list,
    }
    return render(request, 'cart.html', context)
