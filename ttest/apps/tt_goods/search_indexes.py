from haystack import indexes
from .models import GoodsSKU

class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """建立索引时被使用的类"""
    #定义字符类型的属性，名称固定为text
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """从哪个表中查询"""
        return GoodsSKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据"""
        return self.get_model().objects.all()