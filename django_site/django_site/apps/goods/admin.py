from django.contrib import admin
from . import models
from .utils import generate_static_list_search_html, generate_static_sku_detail_html


class GoodsCategoryAdmin(admin.ModelAdmin):
    # 重写
    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        obj.save()
        # 重新生成新的列表静态界面
        generate_static_list_search_html()

    def delete_model(self, request, obj):
        """
        Given a model instance delete it from the database.
        """
        obj.delete()
        # 重新生成新的列表静态界面
        generate_static_list_search_html()


class SKUAdmin(admin.ModelAdmin):
    """商品模型"""

    def save_model(self, request, obj, form, change):
        """当点击admin中的保存按钮时会来调用此方法"""
        obj.save()
        # 重新生成新的商品详情页面
        generate_static_sku_detail_html(obj.id)


class SKUImageAdmin(admin.ModelAdmin):
    """商品的图片"""

    def save_model(self, request, obj, form, change):
        """当点击admin中的保存按钮时会来调用此方法"""
        obj.save()
        # 重新生成新的商品详情页面
        sku = obj.sku
        # 如果当前的SKU商品没有默认图片，就给它设置一张默认图片
        if not sku.default_image_url:
            sku.default_image_url = obj.image.url
            sku.save()
        # 重新生成新的商品详情页面
        generate_static_sku_detail_html(sku.id)

    def delete_model(self, request, obj):
        obj.delete()
        sku = obj.sku
        # 重新生成新的商品详情页面
        generate_static_sku_detail_html(sku.id)


admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage, SKUImageAdmin)
