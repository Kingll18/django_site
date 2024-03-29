from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """自定义分页类"""
    page_size = 2  # 指定默认每页显示多少条数据
    max_page_size = 5  # 每页最大显示多少条数据
    page_size_query_param = 'page_size'  # 前端用来指定每页显示第几页 查询关键字 默认就是page
