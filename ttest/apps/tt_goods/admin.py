from django.contrib import admin
from .models import GoodsCategory,Goods,GoodsSKU,GoodsImage,IndexGoodsBanner,IndexCategoryGoodsBanner,IndexPromotionBanner
from django.shortcuts import render
import os
from django.conf import settings
import time

class GoodsCategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name','logo']
    def save_model(self, request, obj, form, change):
        super().save_model(request,obj, form, change)
        #生成静态页面
        group_html()


    def delete_model(self, request, obj):
        super().delete_model(request,obj)
        # 生成静态页面
        group_html()



def group_html(request):
    time.sleep(2)
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


    response = render(None, 'index.html', context)

    html = response.content.decode()
    with open(os.path.join(settings.GENERATE_HTML,'index.html'),'w') as f1:
        f1.write(html)



admin.site.register(GoodsCategory)
admin.site.register(Goods)
admin.site.register(GoodsSKU)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexCategoryGoodsBanner)
admin.site.register(IndexPromotionBanner)