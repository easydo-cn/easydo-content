# -*- encoding: utf-8 -*-
from zope.security.proxy import removeSecurityProxy

class Quota:

    def __init__(self,context):
        self.context = removeSecurityProxy(context)

    def get_size_limit(self):
        return self.context.settings.get('size_limit')

    def set_size_limit(self, size):

        # 取消容量限制, 删除容量计数
        if size is None:
            if 'size_limit' in self.context.settings:
                del self.context.settings['size_limit']
                del self.context.total_size

        # 更新容量限制
        elif  'size_limit' in self.context.settings:
            self.context.settings['size_limit'] = size

        # 新建容量限制, 设置容量限制，计算容器下的文件总和
        else:
            self.context.settings['size_limit'] = size
            self.context.total_size = self.sum_size()

    def sum_size(self, obj=None):
        # 计算容器下所有文件的总和
        if obj is None:
           obj = self.context

        if hasattr(obj, 'total_size'):
            return obj.total_size

        size = obj.size
        for sub_obj in obj.values():
            if 'Container' in sub_obj.object_types:
                size = size + self.sum_size(sub_obj)
        return size
