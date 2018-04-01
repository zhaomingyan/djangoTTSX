from django.shortcuts import render
from .models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner, GoodsSKU
import os
from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django_redis import get_redis_connection
from django.core.paginator import Paginator, Page
from django.core.cache import cache
from haystack.generic_views import SearchView


# Create your views here.
def index(request):
    # 缓存中读取数据
    context = cache.get('index')

    if context is None:
        # 查询分类信息
        category_list = GoodsCategory.objects.all()

        # 查询轮播图片
        banner_list = IndexGoodsBanner.objects.all().order_by('index')

        # 查询广告
        adv_list = IndexPromotionBanner.objects.all().order_by('index')

        # 查询每个分类的推荐产品
        for category in category_list:
            # 查询推荐的标题商品，当前分类的，按照index排序的，取前3个
            category.title_list = IndexCategoryGoodsBanner.objects.filter(display_type=0, category=category).order_by(
                'index')[0:3]
            # 查询推荐的图片商品
            category.img_list = IndexCategoryGoodsBanner.objects.filter(display_type=1, category=category).order_by(
                'index')[0:4]

        context = {
            'category_list': category_list,
            'banner_list': banner_list,
            'adv_list': adv_list,
        }

        # 缓存数据
        cache.set('index', context, 3600)

    response = render(request, 'index.html', context)

    return response


def detail(request, sku_id):
    # 查询商品详情
    try:
        sku = GoodsSKU.objects.get(pk=sku_id)
    except:
        raise Http404

    # 查询分类信息
    category_list = GoodsCategory.objects.all()

    # 查询新品推荐:当前商品所在分类的最新的两个商品
    # new_list = GoodsSKU.objects.filter(category=sku.category).order_by('-id')[0:2]
    # 一找多：分类对象.模型类小写_set
    # 多找一：sku.category  商品的分类对象
    new_list = sku.category.goodssku_set.all().order_by('-id')[0:2]

    # 查询当前商品的所有的陈列
    # 根据当前sku找到对应的spu
    goods = sku.goods
    # 根据spu找所有的sku
    other_list = goods.goodssku_set.all()

    # 最近浏览的商品
    if request.user.is_authenticated():
        redis_client = get_redis_connection()
        # 构造键
        key = 'history%d' % request.user.id
        # 如果当前编号存在 则删除
        redis_client.lrem(key, 0, sku_id)
        # 如果当前编号不存在  则添加
        redis_client.lpush(key, sku_id)
        # 超过5个，则删除
        if redis_client.llen(key) > 5:
            redis_client.rpop(key)

    context = {
        'sku': sku,
        'category_list': category_list,
        'new_list': new_list,
        'other_list': other_list,

    }
    return render(request, 'detail.html', context)


def list_sku(request, category_id):
    try:
        # 查询当前分类对象
        category_now = GoodsCategory.objects.get(pk=category_id)
    except:
        return Http404
    # 接收排序规则
    order = int(request.GET.get('order', 1))
    if order == 2:
        order_by = '-price'
    elif order == 3:
        order_by = 'price'
    elif order == 4:
        order_by = '-sales'
    else:
        order_by = '-id'

    # 查询当前分类的所有商品
    sku_list = GoodsSKU.objects.filter(category_id=category_id).order_by(order_by)
    # 查询所有分类信息
    category_list = GoodsCategory.objects.all()
    # 最新商品
    new_list = category_now.goodssku_set.all().order_by('-id')[0:2]

    # 分页
    paginato = Paginator(sku_list, 1)
    # 总页数
    total_page = paginato.num_pages
    # 接收页码值，进行判断
    pindex = int(request.GET.get('pindex', 1))
    if pindex < 1:
        pindex = 1
    elif pindex > total_page:
        pindex = total_page

        # 查询指定页码的数据
    page = paginato.page(pindex)

    # 构造页码列表，用于提示页码链接
    page_list = []  # 3 4 5 6 7==> range(n-2,n+3)
    # 如果不足5页，显示所有数字
    if total_page <= 5:
        page_list = range(1, total_page + 1)
    elif pindex <= 2:  # 如果是1到2页，则显示1-5
        page_list = range(1, 6)
    elif pindex > total_page - 1:  # 如果是后两页，则显示最后5页
        page_list = range(total_page - 4, total_page + 1)  # 共18页，则最后的数字是14 15 16 17 18
    else:
        page_list = range(pindex - 2, pindex + 3)

    context = {
        'page': page,
        'category_list': category_list,
        'category_now': category_now,
        'new_list': new_list,
        'order': order,
        'page_list': page_list,
    }
    return render(request, 'list.html', context)


class MySearchView(SearchView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = '搜索结果'
        context['category_list'] = GoodsCategory.objects.all()
        return context
