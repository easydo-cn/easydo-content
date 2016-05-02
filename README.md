# easydo-content

model classes for easydo.cn

## 基础对象

- 条目 Item
  - 文件 File
  - 数据条目 DataItem
- 容器 Container

  container = Container()
  item = container['item1'] = Item()
  
  item.name is 'item1'
  item.parent is contaienr 

## 属性存取

### 基础属性

  item.md['title'] = 'item 1'

### 设置信息

  container.settings['show_comment'] = True

### 扩展属性

  container.mdset['zopen.test:test']['upper'] = True

