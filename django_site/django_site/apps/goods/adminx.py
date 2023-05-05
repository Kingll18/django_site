import xadmin
from . import models


class SKUXadmin(object):
    """商品模型站点管理"""
    list_display = ['id', 'name', 'price', 'stock', 'sales']
    model_icon = 'fa fa-bathtub'  # 模型在菜单栏显示的小图标
    list_editable = ['price', 'stock']
    refresh_times = [3, 5]


xadmin.site.register(models.GoodsCategory)
xadmin.site.register(models.GoodsChannel)
xadmin.site.register(models.Goods)
xadmin.site.register(models.Brand)
xadmin.site.register(models.GoodsSpecification)
xadmin.site.register(models.SpecificationOption)
xadmin.site.register(models.SKU, SKUXadmin)
xadmin.site.register(models.SKUSpecification)
xadmin.site.register(models.SKUImage)

from xadmin import views


class BaseSetting(object):
    """xadmin的基本配置"""
    enable_themes = True  # 开启主题切换功能
    use_bootswatch = True  # 开启更多主题


xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "荣芊商城运营管理系统"  # 设置站点标题
    site_footer = "荣芊商城集团有限公司"  # 设置站点的页脚
    menu_style = "accordion"  # 设置菜单折叠


xadmin.site.register(views.CommAdminView, GlobalSettings)
