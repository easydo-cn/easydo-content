# -*- encoding:utf-8 -*-
from zope.security.proxy import removeSecurityProxy
from zope.annotation.interfaces import IAnnotations

KEY = "edo_content.lists"


class ListsManager:

    def __init__(self, context):
        self.context = removeSecurityProxy(context)
        annotations = IAnnotations(self.context)
        lists = annotations.get(KEY)
        if lists is None:
            from content import Container
            lists = annotations[KEY] = Container()
            lists.__parent__ = self.context
            lists.__name__ = '++lists++'
        self.lists= lists

    def values(self):
        return self.lists.values()

    def keys(self):
        return self.lists.keys()

    def items(self):
        return self.lists.items()

    def get(self, name):
        return self.lists[name]

    def new(self, name, title, description=''):
        name = self.lists.choose_name(name)
        from content import List
        self.lists[name] = List()

        self.lists[name].title = title
        self.lists[name].description = description

        return self.lists[name]

    def clear(self):
        annotations = IAnnotations(self.context)
        if KEY in annotations:
            # 删除所有的清单对象
            annotations_ = annotations[KEY]
            for key in list(annotations_.keys()):
                del annotations_[key]
            del annotations[KEY] 

    def remove(self, name):
        del self.lists[name]

    def move_to(self, name, index):
        keys = list(self.keys())
        keys.remove(name)
        keys.insert(index, name)
        self.lists.set_order(keys)

