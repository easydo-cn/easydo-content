# -*- encoding: utf-8 -*-
from types import StringTypes, TupleType, ListType
from BTrees.OOBTree import OOBTree
from persistent import Persistent
from persistent.list import PersistentList
from acl import ACL, ROLE_MAP
from relation import Relations
from taggroup import TagGroups
from quota import Quota 

from zope.app.container.interfaces import INameChooser
from zope.dublincore.interfaces import IWriteZopeDublinCore, IZopeDublinCore

from zope.container.contained import Contained, setitem, uncontained, notifyContainerModified
from zope.copypastemove.interfaces import IObjectMover, IObjectCopier
from zope.location.interfaces import ISublocations

from annotation import Annotation, MDSet, FieldStorage
from lists import ListsManager

class Object(Persistent, Contained):

    object_types = ('Object', )
    metadata = ()
    allowed_roles = ROLE_MAP.keys()

    @property
    def name(self):
        return self.__name__

    @property
    def parent(self):
        return self.__parent__

    @property
    def relations(self):
        return Relations(self)

    @property
    def acl(self):
        return ACL(self)

    @property
    def md(self):
        return FieldStorage(self)

    @property
    def mdset(self):
        return MDSet(self)

    @property
    def lists(self):
        return ListsManager(self)

    @property
    def settings(self):
        return Annotation(self)

    def move_to(self, target, new_name=None):
        return IObjectMover(self).moveTo(target, new_name)

    def copy_to(self, target, new_name=None, remove_permissions=True):
        return IObjectCopier(self).copyTo(target, new_name, remove_permissions=remove_permissions)

    def add_tag(self, tag):
        """ 添加一个Tag """
        if not tag: return

        tags = list(self.md.get('subjects'))
        if tag in tags: return

        # 得到所在的维度信息
        tag_group = self.parent.tag_groups.get_group_by_tag(tag, flat=True)

        # 如果是单选，去除subject中同一维度的标签
        if tag_group and tag_group['single']:
            for _tag in tags:
                if _tag in tag_group['tags']:
                    tags.remove(_tag)

        self.md.set('subjects', tags + (tag,))

    @property
    def parents(self):
        _parents = []

        context = self.parent
        while not isinstance(context, Root):
            _parents.insert(0, context)
            context = context.parent
        return _parents

class Item(Object):

    data = ''

    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

    # md的快速访问方法

    def __getitem__(self, name, default=None):
        return self.md.get(name, default)

    def __setitem__(self, name, value):
        self.md[name] = value

class Container(Object):

    order_limit = 300
    container_order_limit = 300
    size = 0
    def __init__(self):
        self._data = OOBTree()
        self._order = PersistentList()
        self._container_order= PersistentList()

    def choose_name(self, name, obj=None):
        return INameChooser(self).chooseName(name, obj)

    @property
    def tag_groups(self):
        return TagGroups(self)

    @property
    def quota(self):
        return Quota(self)

    def keys(self):
        for key in self._order:
            yield key

        for key in self._data:
            if key not in self._order:
                yield key

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def values(self):
        return [self._data.get(key) for key in self.keys()]

    def __len__(self):
        return len(self._data)

    def items(self):
        return ((i, self._data.get(i)) for i in self.keys())

    def __contains__(self, key):
        return self._data.has_key(key)

    has_key = __contains__

    def __setitem__(self, key, obj):
        existed = self._data.has_key(key)

        bad = False
        if isinstance(key, StringTypes):
            try:
                unicode(key)
            except UnicodeError:
                bad = True
        else:
            bad = True
        if bad:
            raise TypeError("'%s' is invalid, the key must be an "
                            "ascii or unicode string" % key)
        if len(key) == 0:
            raise ValueError("The key cannot be an empty string")

        # We have to first update the order, so that the item is available,
        # otherwise most API functions will lie about their available values
        # when an event subscriber tries to do something with the container.
        if not existed:
            if len(self._order) < self.order_limit:
                self._order.append(key)
            if len(self._container_order) < self.container_order_limit:
                if 'Container' in getattr(obj, 'object_types', []):
                    self._container_order.append(key)

        # This function creates a lot of events that other code listens to.
        try:
            setitem(self, self._data.__setitem__, key, obj)
        except Exception:
            if not existed:
                if key in self._order: self._order.remove(key)
                if key in self._container_order: self._container_order.remove(key)
            raise

        return key

    def __delSublocations(self, obj):
        subs = ISublocations(obj, None)
        if subs is not None:
            for sub in subs.sublocations():
                sub._v_del = True
                if ISublocations(sub, None):
                    self.__delSublocations(sub)

    def __delitem__(self, name):
        obj = self[name]
        self.__delSublocations(obj)

        uncontained(self._data[name], self, name)
        del self._data[name]

        if name in self._order:
            self._order.remove(name)
        if name in self._container_order:
            self._container_order.remove(name)

    def ordered_keys(self):
        return self._order

    def ordered_container_keys(self):
        return self._container_order

    def ordered_containers(self):
        return (self._data.get(key) for key in self._container_order)

    def set_order(self, order):
        if not isinstance(order, ListType) and \
            not isinstance(order, TupleType):
            raise TypeError('order must be a tuple or a list.')

        for i in order:
            if i not in self:
                raise ValueError('order item not in container.')

        self._order = PersistentList(order)
        notifyContainerModified(self)

    def set_container_order(self, order):
        if not isinstance(order, ListType) and \
            not isinstance(order, TupleType):
            raise TypeError('order must be a tuple or a list.')

        for i in order:
            if i not in self:
                raise ValueError('order item not in container.')

        self._container_order = PersistentList(order)
        notifyContainerModified(self)

    def object_path(self, obj):
        parents = []
        while obj is not self:
            if obj.__name__: parents.insert(0, obj.__name__)
            obj = obj.__parent__
            if obj is None: return None
        return '/'.join(parents)

    def object_by_path(self, path):
        context = self
        for name in filter(lambda i:i != '', path.split('/')):
            context = context.get(name)
            if context is None:
                return

        return context

    def remove(self, name):
        del self[name]


class Root(Container):

    @property
    def parent(self):
        return None

class List(Item):

    title = ""
    description = ""
