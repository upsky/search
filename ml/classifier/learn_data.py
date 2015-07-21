# -*- coding: utf-8 -*-

#
# Learn Data Loader
#

import json
from ..utils.logger import Log

#-------------------------------------------------------------------------------
# helpers for LearnDataLoader.data_tree
def SubTree(cat_node):
    return cat_node[1]

def GetNodeFieldMap(cat_node):
    return cat_node[0]

def GetNodeField(cat_node, field_name, default=None):
    return GetNodeFieldMap(cat_node).get(field_name, default)

def SetNodeField(cat_node, field_name, value):
    GetNodeFieldMap(cat_node)[field_name] = value

def InitNodeField(cat_node, field_name, init_value):
    v = GetNodeField(cat_node, field_name, init_value)
    SetNodeField(cat_node, field_name, v)

#-------------------------------------------------------------------------------
class LearnDataLoader:
    def __init__(self, categories_hier_json=None, train_data_json=None, balance_category_min=0, log=True):
        if categories_hier_json == None or train_data_json == None:
            self.clear()
        else:
            self.load(categories_hier_json, train_data_json, balance_category_min, log)

    #-------------------------------------------------------
    def is_loaded(self):
        return self.is_loaded_flag

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def clear(self):
        self.is_loaded_flag = False
        self.err_msg = None
        self.data_tree = dict()             # обучающие данные
        self.cat_id2path = dict()           # cat id -> ['full', 'category', 'path']
        self.examples = 0                   # кол-во обучающих примеров

    #-------------------------------------------------------
    def dump2obj(self):
        obj = {
            'data_tree': self.data_tree,
            'cat_id2path': self.cat_id2path,
            'examples': self.examples
        }
        return obj

    #-------------------------------------------------------
    def load_from_obj(self, obj):
        self.data_tree = obj['data_tree']
        self.cat_id2path = obj['cat_id2path']
        self.examples = obj['examples']
        self.is_loaded_flag = True

    #-------------------------------------------------------
    # Загружает:
    #   - иерархию категорий, для контроля обучающих данных
    #   - обучающие данные и контролирует правильность категорий обучающих данных
    #   - при balance_category_min > 0 балансирует обучающие данные между категориями;
    #     те суб-категории, в которых обучающих данных меньше balance_category_min,
    #     прилепляет эти данные к родительской категории; и так данные поднимаются
    #     вверх по иерархии пока либо объем категории не станет достаточным, либо
    #     не достигнем корня.
    # returns: true/false, see get_err_msg() for details
    def load(self, categories_hier_json, train_data_json, balance_category_min=0, log=True):
        self.clear()

        if log: Log("Loading hierarchy")
        if not self._load_cats_hier(categories_hier_json):
            return False

        try:
            fd = open(train_data_json)
        except Exception, e:
            self.err_msg = "Can't open file '%s', exc: %s" % (json_file, str(e))
            return False

        if log: Log("Loading data")
        n = 0
        for line in fd:
            n += 1
            line = line.strip()
            if len(line) == 0:
                continue
            try:
                rec = json.loads( line )
            except Exception, e:
                self.err_msg = "Can't parse json train-example at line %d, exc: %s" % (n, str(e))
                return False

            cat_path = rec['cat_path']
            title = rec['title']
            desc = rec['desc']

            if not self._add_data(cat_path=cat_path, data={'title':title, 'desc':desc}):
                return False

            self.examples += 1

        fd.close()
        if log: Log("Loaded %d examples" % self.examples)

        if balance_category_min > 0:
            if log: Log("Balancing to %d examples in category" % balance_category_min)
            self.balance_data(balance_category_min)

        '''
        h = self.get_categories_hier()
        sss = json.dumps( h, ensure_ascii=False, indent=2, sort_keys=True )
        print sss.encode('utf-8')
        '''

        if log: Log("Loading has been done")
        self.is_loaded_flag = True
        return True

    #-------------------------------------------------------
    # returns: list( tuple(int<category_id>, unicode<text>) )
    # fields_to_get Список полей, которые конкатенировать в качестве обучающих текстов;
    #               конткатенация идёт через concat_str.
    def get_learn_data(self, fields_to_get=['title'], concat_str=u' '):
        data = []
        total = LearnDataLoader._recursive_tree2list(self.data_tree, fields_to_get, concat_str, data)
        # print "total: " + str(total)
        return data

    @staticmethod
    def _recursive_tree2list(node, fields_to_get, concat_str, out_data=[]):
        # переменные для контроля кол-ва обучающих примеров
        my = 0
        sub = 0

        for (cat, cat_data) in node.iteritems():
            # идём вглубь
            sub += LearnDataLoader._recursive_tree2list(SubTree(cat_data), fields_to_get, concat_str, out_data)

            # собираем данные
            cat_id = GetNodeField(cat_data, 'id')
            train_data = GetNodeField(cat_data, 'train', None)
            if train_data == None:  # дошли до листа
                continue

            my += len(train_data)
            for d in train_data:
                # конструируем документ из заданных полей
                doc = ''
                for f in fields_to_get:
                    if len(doc) > 0:
                        doc += concat_str
                    doc += d[f]
                out_data.append( (cat_id, doc) )

        return (my + sub)

    #-------------------------------------------------------
    # returns None if no such id, or full category path: ['cat', 'subcat', ...]
    def get_cat_id2path(self, cat_id):
        return self.cat_id2path.get(cat_id, None)

    #-------------------------------------------------------
    # Коприует дерево, без данных - только "визуальную" часть + id категорий + train_num (кол-во обуч. примеров в кат).
    # remain_data   Имена полей из дескриптора категории, которые оставить (кроме id, он и так останется).
    # returns: {'cat':({'id':0, 'train_num':10}, {SubTree}), ...}
    def get_categories_hier(self, remain_data=[]):
        dst_tree = dict()
        total = LearnDataLoader._recursive_get_cats(self.data_tree, dst_tree, remain_data)
        # print total
        return dst_tree

    @staticmethod
    def _recursive_get_cats(node, dst_tree, remain_data):
        # счётчики контроля кол-ва обучающих примеров
        my = 0
        subs = 0

        for (cat, cat_data) in node.iteritems():
            # коприуем данные ноды
            desc = GetNodeFieldMap(cat_data)
            dst_desc = {}
            dst_desc['id'] = desc['id']
            dst_desc['train_num'] = len(desc['train']) if desc.get('train', None) != None else 0
            my += dst_desc['train_num']

            for r in remain_data:
                d = desc.get(r, None)
                dst_desc[r] = d

            dst_tree[cat] = ( dst_desc, {} )
            # идём глубже
            sub_node = SubTree( cat_data )
            dst_sub_tree = SubTree( dst_tree[cat] )
            subs += LearnDataLoader._recursive_get_cats(sub_node, dst_sub_tree, remain_data)

        return (my + subs)

    #-------------------------------------------------------
    # returns: sorted list(cat_id)
    def get_cats_ids_list(self):
        cats_ids_list = []
        LearnDataLoader._recursive_get_cats_ids(self.data_tree, cats_ids_list)
        cats_ids_list = sorted(cats_ids_list)
        return cats_ids_list

    @staticmethod
    def _recursive_get_cats_ids(tree, cats_ids_list):
        for (cat, cat_data) in tree.iteritems():
            cat_id = GetNodeField(cat_data, 'id')
            cats_ids_list.append( cat_id )

            sub_tree = SubTree( cat_data )
            LearnDataLoader._recursive_get_cats_ids(sub_tree, cats_ids_list)


    #-------------------------------------------------------
    # Балансирует дерево с обучающими данными - чтобы в подкатегориях
    # было не менее balance_category_min примеров.
    def balance_data(self, balance_category_min):
        # data_tree: { 'cat':tuple( {'id':1, 'data':[]}, {'subcat':tuple(...)} ) }
        self._recursive_balance_data( self.data_tree, balance_category_min )

    def _recursive_balance_data(self, tree, balance_category_min, level=0, path=u''):
        # добрались до листа
        if len(tree) == 0:
            return None

        up_data = []

        # "поднимаем" все данные из листовых категорий
        for (cat, cat_data) in tree.iteritems():
            curr_path = unicode(path) + '/' + cat

            data = GetNodeField(cat_data, 'train', None)
            if data == None:            # дошли до листа
                continue

            # поднимаем к этой ноде все данные дочерних элементов, у которых элементов мало
            sub_data = self._recursive_balance_data( SubTree(cat_data), balance_category_min, level+1, curr_path )
            if sub_data != None:
                data.extend( sub_data )

            # если в текущей ноде данных всё равно мало, добавляем их к общей куче, которая пойдёт "наверх"
            if len(data) < balance_category_min:
                up_data.extend( data )
                del data[:]     # удаляем содержимое текущего элемента

        # что-то накопили, что нужно поднять выше
        if len(up_data) > 0:
            return up_data

        # хватает, оставляем у себя то, что скопили
        return None

    #-------------------------------------------------------
    # загружает из json-файла структуру категорий, сохраняя в 2х видах: виз
    def _load_cats_hier(self, categories_hier_json):
        # загружаем
        self.data_tree = dict()

        try:
            fd = open(categories_hier_json)
            self.data_tree = json.load( fd )
        except Exception, e:
            self.err_msg = "Can't load file '%s', exc: %s" % (categories_hier_json, str(e))
            return False

        # составляем мапу cat_id2path
        self.cat_id2path = dict()
        LearnDataLoader._recursive_make_id2path(self.data_tree, self.cat_id2path)
        return True

    @staticmethod
    def _recursive_make_id2path(tree, cat_id2path, path=[]):
        for (cat, cat_data) in tree.iteritems():
            # получаем путь
            curr_path = list(path)
            curr_path.append( cat )
            # сохраняем
            i = GetNodeField(cat_data, 'id')
            cat_id2path[i] = curr_path
            # идём глубже
            LearnDataLoader._recursive_make_id2path(SubTree(cat_data), cat_id2path, curr_path)

    #-------------------------------------------------------
    '''
    self.data_tree structure:
    {
        'Курьерские услуги': (                                      # category name -> tuple with 2 items
            {'id':1, 'data': [{'title':'..', 'desc':'..'}, ...] },  # 0 item is cat-descriptor: category id and training data
            {                                                       # 1 item: nested sub-categories with same sturct
                'Услуги пешего курьера': (
                    {'id':2, 'data': ...},
                    { ..sub categories with the same nesting hier.. }
                )
            }
        ),
        'Another category': (
            ...
        ),
        ...
    }
    '''
    #-------------------------------------------------------
    def _add_data(self, cat_path, data):
        # check and get leaf node
        curr_path = ''
        node = self.data_tree
        node_data = None

        for cat in cat_path:
            if len(curr_path) > 0:
                curr_path += '/'
            curr_path += cat
            node_data = node.get(cat, None)
            if node_data == None:
                self.err_msg = "You're trying to add training data to category '%s', but no such category in our hierarchy found" % curr_path
                return False
            node = SubTree(node_data)

        InitNodeField(node_data, 'train', [])
        GetNodeField(node_data, 'train').append( data )
        return True
