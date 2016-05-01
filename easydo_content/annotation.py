# -*- encoding:utf-8 -*-
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from zope.annotation.interfaces import IAnnotations
from zope.dublincore.interfaces import IZopeDublinCore

def make_persistent(value):
    if type(value) == list:
        return PersistentList([make_persistent(i) for i in value])
    elif type(value) == dict:
        return PersistentDict([(i[0], make_persistent(i[1])) for i in value.items()])
    return value

class Annotation:
    """ 基于annotaion的操作，默认就是设置"""

    key = "_settings"

    def __init__(self, context):
        self.context = context

    def keys(self):
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        if not formdata:
            return []
        return [key for key in formdata if key[0] != '_']

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, field_name):
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        if not formdata:
            return False
        return formdata.has_key(field_name)

    def __delitem__(self, field_name):
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        del formdata[field_name]

    # XXX 这个应该不需要，没价值
    def _values(self):
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        if not formdata:
            return []
        return formdata.values()

    def items(self):
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        if not formdata:
            return []
        return [(key, value) for key, value in formdata.items() if key[0] != '_']

    def has_key(self, key):
        """判断是否存在某个字段"""
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        if formdata is None:
            return False
        else:
            return formdata.has_key(key)

    def __setitem__(self, field_name, value):
        """ 保存一个字段，支持dublincore """
        value = make_persistent(value)

        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key)
        if not formdata:
            formdata = annotations[self.key] = PersistentDict()
        formdata[field_name] = value

    def __getitem__(self, field_name, default=None):
        """ 读取一个字段，支持dublincore """
        annotations = IAnnotations(self.context)
        formdata = annotations.get(self.key, {})
        if field_name in formdata:
            return formdata[field_name]
        elif field_name in ['start', 'end']:  # 和之前的兼容
            return self.context.__dict__.get(field_name, default)
        else:
            return default

    def set(self, field_name, value):
        assert(value is not None)
        self[field_name] = value

    def get(self, field_name, default=None, inherit=False):
        if not inherit:
            return Annotation.__getitem__(self, field_name, default)
        else:
            current = self.context
            while current.parent is not None and Annotation(current).get(field_name) is None:
                current = current.parent
            return Annotation(current).get(field_name, default)

    def update(self, **kw):
        for name, value in kw.items():
            self[name] = value

    def remove(self,name):
        del IAnnotations(self.context)[self.key][name]

    def clear(self):
        try:
            del IAnnotations(self.context)[self.key]
        except KeyError:
            pass

class MDSet(Annotation):

    key = "zopen.metadata.extended_metadata"

    def new(self, name):
        metadatas = IAnnotations(self.context).setdefault(self.key, PersistentDict())
        if name not in metadatas:
            metadatas[name] = PersistentDict()
        return metadatas[name]

    def get(self, field_name, default={}, inherit=False):
        if not inherit:
            return self.__getitem__(field_name, default)
        else:
            current = self.context
            while current.parent is not None and MDSet(current).get(field_name, None) is None:
                current = current.parent
            return MDSet(current).get(field_name, default)

DUBLIN = ["title", "description", "identifier", "creators", "subjects",
          "created", "modified", "expires", "effective", "contributors"]

class FieldStorage(Annotation):

    key = "zopen.formgen"

    def keys(self):
        return Annotation.keys(self) + DUBLIN

    def __contains__(self, key):
        return Annotation.__contains__(self, key) or key in DUBLIN

    def dublin_get(self, key, default=None):
        assert(key in DUBLIN)
        return getattr(IZopeDublinCore(self.context), key, default)

    def dublin_set(self, key, value):
        assert(key in DUBLIN)
        return setattr(IZopeDublinCore(self.context), key, value)

    def dublin_items(self):
        return [(key, getattr(IZopeDublinCore(self.context), key)) for key in DUBLIN]

    def get(self, field_name, default=None, inherit=False):
        if not inherit:
            return self.__getitem__(field_name, default)
        else:
            current = self.context
            while current.parent is not None and FieldStorage(current).get(field_name) is None:
                current = current.parent
            return FieldStorage(current).get(field_name, default)

    def items(self):
        return self.dublin_items() + Annotation.items(self)

    def __setitem__(self, field_name, value):
        """ 保存一个字段，支持dublincore """
        #内置变量
        if field_name in DUBLIN:
            if isinstance(value, basestring):
                value = unicode(value)
            elif isinstance(value, (list, tuple, PersistentList)):
                value = PersistentList([unicode(v)  for v in value])
            elif value is None:
                return

            setattr(IZopeDublinCore(self.context), field_name, value)

        else:
            Annotation.__setitem__(self, field_name, value)

    def __getitem__(self, field_name, default=None):
        """ 读取一个字段，支持dublincore """
        if field_name in DUBLIN:
            return self.dublin_get(field_name, default)
        return Annotation.__getitem__(self, field_name, default)

