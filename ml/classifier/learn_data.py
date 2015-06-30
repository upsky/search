# -*- coding: utf-8 -*-

#
# Learn Data Loader
#

import json

kMinimalCategoryLearnExamples = 10

#-------------------------------------------------------------------------------
class LearnDataLoader:
    def __init__(self, categories_hier_json=None, train_data_json=None):
        if categories_hier_json == None or train_data_json == None:
            self.clear()
        else:
            self.load(categories_hier_json, train_data_json)

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def is_ok(self):
        return (self.err_msg == None)

    #-------------------------------------------------------
    def clear(self):
        self.err_msg = None
        self.visible_cats_hier = None       # иерархия категорий для показа наружу; имеет упорядоченность в элементах
        self.checking_cats_hier = None      # просто деревянная структура для внутренних проверок
        self.data_tree = dict()                  # обучающие данные
        self.examples = 0

    #-------------------------------------------------------
    # returns: [ {'name':'cat', 'subcats':[..nesting..]}, ... ]
    def get_categories_hier(self):
        return self.visible_cats_hier

    #-------------------------------------------------------
    # returns True/False; False - something wrong/unexpected in structure
    def set_categories_hier(self, hier):
        self.visible_cats_hier = hier
        self.checking_cats_hier = dict()
        return self._recursive_copy_cats_hier(self.visible_cats_hier, self.checking_cats_hier)

    #-------------------------------------------------------
    # returns: list( tuple(['category','path'], {'title':'..', 'desc':'..'}) )
    def get_learn_data(self):
        data = []
        self._recursive_tree2list(self.data_tree, data)
        return data

    #-------------------------------------------------------
    def balance_data(self):
        self._recursive_balance_data( self.data_tree )

    #-------------------------------------------------------
    def _recursive_balance_data(self, tree, level=0, path=u''):
        up_data = []

        # сначала "поднимаем" все данные из листовых категорий
        for (cat, sub_tree) in tree.iteritems():
            if cat == '__data__':
                continue

            curr_path = unicode(path) + '/' + cat

            sub_data = self._recursive_balance_data( sub_tree, level+1, curr_path )
            if sub_data != None:
                up_data.extend( sub_data )
                del sub_data[:]

        # print ">%d. path: %s" % (level, path.encode('utf-8'))

        # добавляем "поднятое" к своим данным
        # - у корневного элемента нет обучающих данных
        if level == 0:
            if len(up_data) > 0:
                raise Exception("Too few training data")
            return None

        data = tree.get('__data__', None)
        if data == None:
            raise Exception("_recursive_balance_data(): No __data__ field!")
        data.extend( up_data )

        # - теперь проверяем в текущей ноде, хватает ли объёма обучающих данных
        if len(data) < kMinimalCategoryLearnExamples:
            return data

        # - хватает, оставляем у себя то, что скопили
        return None

    #-------------------------------------------------------
    def load(self, categories_hier_json, train_data_json):
        self.clear()

        if not self.load_cats_hier(categories_hier_json):
            return False

        try:
            fd = open(train_data_json)
        except Exception, e:
            self.err_msg = "Can't open file '%s', exc: %s" % (json_file, str(e))
            return False

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

            cat = rec['cat']
            sub_cat = rec['sub_cat']
            title = rec['title']
            desc = rec['desc']

            cat_path = [cat, sub_cat]
            if cat == sub_cat or len(sub_cat) == 0:
                cat_path = [cat]

            if not self._add_data(cat_path=cat_path, data={'title':title, 'desc':desc}):
                return False

            self.examples += 1

        fd.close()
        return True

    #-------------------------------------------------------
    def load_cats_hier(self, categories_hier_json):
        self.visible_cats_hier = None
        self.checking_cats_hier = None

        try:
            fd = open(categories_hier_json)
            self.visible_cats_hier = json.load( fd )
        except Exception, e:
            self.err_msg = "Can't load file '%s', exc: %s" % (categories_hier_json, str(e))
            return False

        return self.set_categories_hier(self.visible_cats_hier)

    #-------------------------------------------------------
    def _recursive_copy_cats_hier(self, hier_from, hier_to, path=''):
        if hier_from == None:
            return True

        for cat in hier_from:
            cat_name = cat.get('name', None)
            sub_cats = cat.get('subcats', None)

            if cat_name == None:
                self.err_msg = "Error in categories hierarchy: tree-path: '%s', field 'name' expected but not found" % path
                return False
            curr_path = unicode(path) + u'.' + cat_name

            hier_to[cat_name] = hier_to.get(cat_name, dict())
            self._recursive_copy_cats_hier(sub_cats, hier_to[cat_name], curr_path)

        return True

    #-------------------------------------------------------
    '''
    self.data_tree structure:
    {
        'Курьерские услуги': {                                  # category name
            '__data__': [{'title':'..', 'desc':'..'}, ...],     # training data
            'Услуги пешего курьера': {                          # subcategory name
                '__data__': [...],
                ...
            },
            ...
        }
    }
    '''
    #-------------------------------------------------------
    def _add_data(self, cat_path, data):
        node = self.data_tree
        check_node = self.checking_cats_hier
        curr_path = ''

        for cat in cat_path:
            # check
            if len(curr_path) > 0:
                curr_path += '/'
            curr_path += cat
            check_node = check_node.get(cat, None)
            if check_node == None:
                self.err_msg = "You're trying to add training data to category '%s', but no such category in our hierarchy found" % curr_path
                return False
            # add
            node[cat] = node.get(cat, {'__data__':[]})
            node = node[cat]

        node['__data__'].append( data )
        return True

    #-------------------------------------------------------
    def _recursive_tree2list(self, node, data=[], path=[]):
        for (cat, sub_node) in node.iteritems():
            if cat == '__data__':
                continue

            # в субкатегории нет обучающих данных
            sub_data = sub_node['__data__']
            if len(sub_data) == 0:
                continue

            curr_path = list(path)
            curr_path.append( cat )

            for d in sub_data:
                data.append( (list(curr_path), d) )

            self._recursive_tree2list(sub_node, data, curr_path)

