# -*- coding: utf-8 -*-

#
# Learn Data Loader
#

import json

from ...logger import Log

#-------------------------------------------------------------------------------
class LearnDataLoader:
    #-------------------------------------------------------
    def __init__(self):
        self.data_tree = {}
        self.cat_id2path = {}

    #-------------------------------------------------------
    def load(self, learn_file):
        learn_data = None
        try:
            Log("Loading json-learn-data file")
            with open(learn_file) as fd:
                learn_data = fd.read()
        except Exception, e:
            raise Exception("Can't load file %s, exc: %s" % (learn_file, str(e)))

        self.loads( learn_data )

    #-------------------------------------------------------
    def loads(self, learn_data_str):
        # загружаем строку и проверяем json-формат
        ldata = None
        try:
            Log("Parsing json-learn-data")
            ldata = json.loads( learn_data_str )
        except Exception, e:
            raise Exception("Bad-formed json format, exc: %s" % str(e))

        # проверяем формат самих данных, заодно формируя id категорий и сохраняя эти id в структурах
        Log("Checking learn-data format")
        cat_id2path = dict()
        nums = [0, 0]   # categories number, learn examples number

        self._recursive_check_format(ldata, cat_id2path, nums)

        Log("Successfully parsed learn-data. Loaded categories: %d, learn examples: %d" % (nums[0], nums[1]))

        # сохраняем
        self.data_tree = ldata
        self.cat_id2path = cat_id2path

    def _recursive_check_format(self, ldata, cat_id2path, nums, path=[]):
        if not type(ldata) is dict:
            raise Exception("Format error, catalog path '%s'. Learn section type must be dict ({})" \
                            % LearnDataLoader.path_arr2str(path))

        categories = ldata.get('categories', None)
        if categories == None:
            return

        for (cat, cat_data) in categories.iteritems():
            cur_path = list(path)
            cur_path.append(cat)

            cat_id = cat_data.get('id', None)
            # назначаем id категории, если такого ещё нет
            if cat_id == None:
                cat_id = nums[0]
                cat_data['id'] = cat_id

            # сохраняем соответствие id категории к её пути
            if cat_id in cat_id2path:
                raise Exception("Duplicating categories ids id=%d" % cat_id)

            cat_id2path[cat_id] = cur_path

            # добавляем id категории, если его ещё нет
            nums[0] += 1

            # если есть обучающие примеры, то их тип должен быть list
            ldata = cat_data.get('learn_data', None)
            if ldata != None:
                if not type(ldata) is list:
                    raise Exception("Format error, catalog path: '%s'. Type of 'learn_data' must be array ([])" \
                                    % LearnDataLoader.path_arr2str(cur_path))
                nums[1] += len(ldata)

            self._recursive_check_format(cat_data, cat_id2path, nums, cur_path)

    #-------------------------------------------------------
    def dump2obj(self):
        obj = {
            'data_tree': self.data_tree,
            'cat_id2path': self.cat_id2path
        }
        return obj

    #-------------------------------------------------------
    def load_from_obj(self, obj):
        data_tree = obj.get('data_tree', None)
        cat_id2path = obj.get('cat_id2path', None)

        if data_tree == None:
            raise Exception("Can't load learn-data from obj. There is no necessary item 'data_tree'")
        if cat_id2path == None:
            raise Exception("Can't load learn-data from obj. There is no necessary item 'cat_id2path'")

        self.data_tree = data_tree
        self.cat_id2path = cat_id2path

    #-------------------------------------------------------
    # Возвращает дерево категорий без обучающих данных - только "визуальную" часть + id категорий.
    def get_categories_tree(self):
        dst_tree = {}
        LearnDataLoader._recursive_get_cats_tree(self.data_tree, dst_tree)
        return dst_tree

    @staticmethod
    def _recursive_get_cats_tree(data_tree, dst_tree):
        children = data_tree.get('categories', None)
        if children == None:
            return

        dst_tree['categories'] = {}
        dst_tree = dst_tree['categories']

        for (cat, cat_data) in children.iteritems():
            dst_tree[cat] = {}
            sub_tree = dst_tree[cat]
            sub_tree['id'] = cat_data['id']
            # рекурсивно погружаемся
            LearnDataLoader._recursive_get_cats_tree(cat_data, sub_tree)

    #-------------------------------------------------------
    # returns: list( tuple(int<category_id>, unicode<text>) )
    def get_learn_data(self):
        out_data = []
        total = LearnDataLoader._recursive_tree2list(self.data_tree, out_data)
        # print "total: " + str(total)
        return out_data

    @staticmethod
    def _recursive_tree2list(data_tree, out_data=[]):
        children = data_tree.get('categories', None)
        if children == None:
            return 0

        my = 0
        sub = 0
        for (cat, cat_data) in children.iteritems():
            cat_id = cat_data['id']

            ldata = cat_data.get('learn_data', None)
            if ldata != None:
                my += len(ldata)
                for ex in ldata:
                    out_data.append( (cat_id, ex) )

            # идём вглубь
            sub += LearnDataLoader._recursive_tree2list(cat_data, out_data)

        return (my + sub)

    #-------------------------------------------------------
    # returns: sorted list(cat_id)
    def get_cats_ids_list(self):
        cats_ids_list = []
        LearnDataLoader._recursive_get_cats_ids(self.data_tree, cats_ids_list)
        cats_ids_list = sorted(cats_ids_list)
        return cats_ids_list

    @staticmethod
    def _recursive_get_cats_ids(data_tree, cats_ids_list):
        children = data_tree.get('categories', None)
        if children == None:
            return

        for (cat, cat_data) in children.iteritems():
            cat_id = cat_data['id']
            cats_ids_list.append( cat_id )
            # идём вглубь
            LearnDataLoader._recursive_get_cats_ids(cat_data, cats_ids_list)

    #-------------------------------------------------------
    @staticmethod
    def path_arr2str(path_arr):
        s = '/' + '/'.join(path_arr)
        return s.encode('utf8')

    '''
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
    '''
