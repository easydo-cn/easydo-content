#coding:utf8
from zope.annotation.interfaces import IAnnotations
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from persistent.dict import PersistentDict
from BTrees.IIBTree import IISet
from BTrees.OOBTree import OOBTree
from zope.security.proxy import removeSecurityProxy

RELATIONS_TARGET = 'zopen.relationsi.target'
RELATIONS_SOURCE= 'zopen.relationsi.source'
RELATION_RECYCLE = 'zopen.relation_recycle'

class Relations(object):

    def __init__(self, context):
        self.context = removeSecurityProxy(context)
        self._target = IAnnotations(self.context).get(RELATIONS_TARGET)
        self._source = IAnnotations(self.context).get(RELATIONS_SOURCE)

    def keys(self):
        if self._target is not None:
            return self._target.keys()
        return []

    def list_relations(self):
        """ 对象所有的关系 """
        if self._target is not None:
            types = self._target.keys()
            return dict([t, self.list_sources(t)] for t in types
                if self.list_sources(t))

    def add(self, relation_type, obj, metadata={}):
        """ 添加关系 """
        # 附件关系不能重复
        stati = getattr(obj, 'stati', ())
        if relation_type == 'attachment' and 'attach.attachment' in stati:
            # 主文件存在才抛出错误
            if obj.relations.list_sources('attachment'):
                raise ValueError('can not attach attachment')

        if self._target is None:
            self._target = IAnnotations(self.context)[RELATIONS_TARGET] = PersistentDict()

        all_targets = self._target.get(relation_type)
        if all_targets is None:
            all_targets = self._target[relation_type] = OOBTree()

        # 加到关系列表中
        obj_id = getUtility(IIntIds).getId(obj)
        if obj_id in all_targets:
            # 已经在关系列表中， 无需添加到被关联列表
            return

        all_targets[obj_id] = PersistentDict(metadata)

        # 加到被关联列表中
        Relations(obj)._add_source(relation_type, self.context)

        # 附件关系改变状态
        if relation_type == 'attachment':
            self.context.state.set('attach.master')
            obj.state.set('attach.attachment')

    def _add_source(self, relation_type, obj):
        if self._source is None:
            self._source = IAnnotations(self.context)[RELATIONS_SOURCE] = PersistentDict()

        all_sources = self._source.get(relation_type)
        if all_sources is None:
            all_sources = self._source[relation_type] = IISet([])

        #加到被关系列表中
        all_sources.add(getUtility(IIntIds).getId(obj))

    def remove(self, relation_type, obj):
        '''删除关系'''
        all_targets = self._target.get(relation_type)
        obj_id = getUtility(IIntIds).getId(obj)
        try:
            del all_targets[obj_id]
        except:
            #obj_id 不在关联列表中，有可能是因为intid变化了，重复删除了
            return

        # 删除被关联信息
        Relations(obj)._remove_source(relation_type, self.context)

        # 改变附件状态
        if relation_type == 'attachment':
            obj.state.set('attach.none')

        # 改变主文件的状态
        if relation_type == 'attachment' and not all_targets:
            self.context.state.set('attach.none')

    def _remove_source(self, relation_type, obj):
        all_sources = self._source.get(relation_type)
        obj_id = getUtility(IIntIds).getId(obj)

        try:
            all_sources.remove(obj_id)
        except:
            #obj_id 不在被关联列表中，有可能是因为intid变化了，或者重复删除了
            return

    def list_targets(self, relation_type):
        '''列出所有关联对象'''
        if self._target is None:
            return []

        all_targets = self._target.get(relation_type, {})
        intids = getUtility(IIntIds)
        result = filter(lambda x: x is not None, [intids.queryObject(i) for i in all_targets.keys()])
        # 即便删除也能找到list_targets
        if not result:
            recycle_targets = IAnnotations(self.context).get(RELATION_RECYCLE)
            if recycle_targets:
                all_targets = recycle_targets.get(relation_type, {})
                result = filter(lambda x: x is not None, [intids.queryObject(i) for i in all_targets.keys()])
        return result

    def has_target(self, relation_type):
        if self._target is None:
            return False
        return bool(self._target.get(relation_type, {}))

    def list_sources(self, relation_type):
        '''列出所有被关联的对象'''
        if self._source is None:
            return []

        all_sources = self._source.get(relation_type, [])
        intids = getUtility(IIntIds)
        return filter(lambda x: x is not None, [intids.queryObject(i) for i in all_sources])

    def has_source(self, relation_type):
        if self._source is None:
            return False
        return bool(self._source.get(relation_type, []))

    def set_metadata(self, relation_type, obj, metadata={}):
        if self._target.get(relation_type) is None:
            return
        obj_id = getUtility(IIntIds).getId(obj)
        if self._target[relation_type].get(obj_id) is None:
            return
        self._target[relation_type][obj_id].update(metadata)

    set_target_metadata = set_metadata

    def get_metadata(self, relation_type, obj):
        if self._target is None:
            return

        metadata = self._target.get(relation_type, {}).get(getUtility(IIntIds).getId(obj), {})
        return dict(metadata)

    get_target_metadata = get_metadata

    def clean(self):
        """清除所有的关系"""
        intids = getUtility(IIntIds)
        intid = intids.queryId(self.context) or intids.getRecycleObjectId(self.context)
        if self._target:
            for relation in self.keys():
                for target in self.list_targets(relation):
                    try:
                        Relations(target)._source[relation].remove(intid)
                    except KeyError:
                        # 被关系表中已经没有这个记录
                        pass

        if self._source:
            for relation in self._source.keys():
                for target in self.list_sources(relation):
                    try:
                        relation_dict = Relations(target)._target[relation]
                        del relation_dict[intid]
                    except KeyError:
                        # 被关系表中已经没有这个记录
                        pass

        # 删除自身的所有关系记录
        anns = IAnnotations(self.context)
        if RELATIONS_TARGET in anns: del anns[RELATIONS_TARGET]
        if RELATIONS_SOURCE in anns: del anns[RELATIONS_SOURCE]
