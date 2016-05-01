# -*- encoding: utf-8 -*-
import json
from zope.security.proxy import removeSecurityProxy
from zope.annotation.interfaces import IAnnotations
from persistent.list import PersistentList

FACETAG_KEY = "zopen.facetag"
FACETAG_INHERIT_KEY = "zopen.facetag.inherit"
FACETAG_REQUIRED_KEY = "zopen.facetag.required"
FACETAG_RADIOS_KEY = "zopen.facetag.radios"

class TagGroups:

    def __init__(self,context):
        self.context = removeSecurityProxy(context)
        annotations = IAnnotations(self.context)
        facetag_data = annotations.get(FACETAG_KEY)
        facetag_inherit = annotations.get(FACETAG_INHERIT_KEY)
        if facetag_data is None:
            facetag_data = annotations[FACETAG_KEY] = PersistentList()
        if facetag_inherit is None:
            facetag_inherit = annotations[FACETAG_INHERIT_KEY] = True

        self.facetag_data = facetag_data
        self.facetag_inherit = facetag_inherit

    def _getList(self, text, pre_count=0):
        temp_list = []
        temp_text = []
        return_text = []
        count = int(text[0][0])
        if count - pre_count > 1:
            raise 'input error'
        temp_id = 0
        for temp in text:
            if temp.startswith(str(count)):
                temp_list.append(temp_id)
            temp_id += 1
        if len(temp_list) == 0:
            return text
        if len(temp_list) == 1:
            return_text.append(text[0])
            if len(text[1:]) != 0:
                return_text.append(self._getList(text[1:],count))
        if len(temp_list) > 1:
            for i in range(len(temp_list)):
                if i != len(temp_list) - 1:
                    if len(text[temp_list[i]+1:temp_list[i+1]]) != 0:
                        temp_text.append(text[temp_list[i]])
                        temp_text.append(self._getList(text[temp_list[i]+1:temp_list[i+1]],count))
                        return_text.append(temp_text)
                        temp_text = []
                    else:
                        return_text.append(text[temp_list[i]])
                else:
                    if len(text[temp_list[i]:]) > 1:
                        temp_text.append(text[temp_list[i]])
                        temp_text.append(self._getList(text[temp_list[i]+1:],count))
                        return_text.append(temp_text)
                        temp_text = []
                    else:
                        return_text.append(text[temp_list[i]])
        return return_text

    def _getText(self, text_list):
        return_data = []
        for data in text_list:
            if isinstance(data, (list, PersistentList)):
                return_data.extend(self._getText(data))
            else:
                count = int(data[0])
                data = list(data)
                data.remove(data[0])
                data = ''.join([x for x in data])
                data = '-' * count + data

                end_str = ''
                if count == 0 and data in self.list_radios():
                    end_str += '#'
                if count == 0 and data in self.list_required():
                    end_str += '*'
                data += end_str

                return_data.append(data)

        return return_data

    def export_text(self):
        """ 得到face tag 文字 """
        return '\n'.join(self._getText(self.facetag_data))

    def import_text(self, text):
        """ 设置face tag文字，会自动转换的, 典型如下:
            按产品
            -wps
            -游戏
            --天下
            --传奇
            -毒霸
            按部门
            -研发
            -市场
        """
        if text == u'':
            required, radios = PersistentList([]), PersistentList([])
            return_text = PersistentList([])
        else:
            text = text.replace(u'\uff0d', u'-')
            text = text.replace(u'\u2014', u'-')
            text_list = text.split('\n')
            required, radios = PersistentList([]), PersistentList([])
            return_text_list = PersistentList([])
            for index, text in enumerate(text_list):
                if text.find('\r') != -1:
                    text = text[:text.index('\r')]
                text = text.strip()
                count = 0
                for stext in list(text):
                    if stext == u'-':
                        if index == 0:
                            raise
                        else:
                            count += 1
                    else:
                        break
                if text == u'\r' or text == u'':
                    continue
                if count != 0:
                    while text.startswith(u'-'):
                        temp_text = list(text)
                        temp_text.remove(u'-')
                        text = ''.join(temp_text)
                    text = text.lstrip(' ')
                    text = str(count) + text
                else:
                    start_str, end_str = text[:-2], text[-2:]
                    require, radio = False, False
                    if '*' in end_str:
                        require = True
                        end_str = end_str.replace('*', '', 1)
                    if '#' in end_str:
                        radio = True
                        end_str = end_str.replace('#', '', 1)

                    text = start_str + end_str
                    if require:
                        required.append(text)
                    if radio:
                        radios.append(text)

                    text = text.lstrip(' ')
                    text = str(0) + text

                return_text_list.append(text)

            return_text = PersistentList(self._getList(return_text_list))

        annotations = IAnnotations(self.context)
        annotations[FACETAG_KEY] = return_text
        annotations[FACETAG_REQUIRED_KEY] = required
        annotations[FACETAG_RADIOS_KEY] = radios

    setFaceTagText = import_text

    def getFaceTagSetting(self):
        """ 得到全部的face tag setting
            [(按产品, (wps, (游戏, (天下, 传奇)), 毒霸)),
             (按部门, (研发, 市场))]
        """
        return self.facetag_data

    def set_inherit(self, flag=True):
        """ 继承上层设置，标签组是上层标签组设置的补充 """
        annotations = IAnnotations(self.context)
        annotations[FACETAG_INHERIT_KEY] = flag
    def get_inherit(self):
        annotations = IAnnotations(self.context)
        return annotations[FACETAG_INHERIT_KEY]
    inherit = property(get_inherit, set_inherit)

    def check(self, tags):
        pass

    def _build_tag(self, tags, group=False):
        children = []

        len_tags = len(tags)
        for index, value in enumerate(tags):
            next_tag = None
            title = value[1:]
            if group:
                dict_tag = {
                    'group': title,
                    'required': title in self.list_required(),
                    'single': title in self.list_radios(),
                    'tags': [],
                }
            else:
                dict_tag = {'name': title}

            if index != len_tags - 1:
                next_tag = tags[index + 1]
                if isinstance(next_tag, (PersistentList, list)):
                    if next_tag[0][0] != value[0]:
                        if group:
                            dict_tag['tags'] = self._build_tag(next_tag)
                        else:
                            dict_tag['children'] = self._build_tag(next_tag)

            if isinstance(value, (PersistentList, list)):
                if next_tag:
                    if next_tag[0][0] == value[0]:
                        continue
                    else:
                        dict_tag = self._build_tag(value)[0]
                else:
                    if tags[0][0] == '0':
                        continue
                    else:
                        dict_tag = self._build_tag(value)[0]

            children.append(dict_tag)

        return children

    def list_items(self):
        tags = self.getFaceTagSetting()
        if not tags:
            return []

        items = []
        for tag in tags:
            if isinstance(tag, basestring):
                items.append(self._build_tag(tags, True)[0])
                break
            else:
                items.append(self._build_tag(tag, True)[0])

        return json.dumps(items)

    def get_group_by_tag(self):
        pass

    def list_required(self):
        """ 必填标签组 """
        annotations = IAnnotations(self.context)
        required = annotations.get(FACETAG_REQUIRED_KEY, None)

        if required != None:
            return required
        else:
            return []

    def list_radios(self):
        """ 单选标签组 """
        annotations = IAnnotations(self.context)
        radios = annotations.get(FACETAG_RADIOS_KEY, None)

        if radios != None:
            return radios
        else:
            return []
