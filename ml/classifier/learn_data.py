# -*- coding: utf-8 -*-

#
# Learn Data Loader
#

import json

#-------------------------------------------------------------------------------
class LearnDataLoader:
    def __init__(self, json_file=None):
        if json_file == None:
            self.clear()
        else:
            self.load(json_file)

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def is_loaded(self):
        return (len(self.tree) > 0)

    #-------------------------------------------------------
    def clear(self):
        self.err_msg = None
        self.tree = dict()
        self.examples = 0

    #-------------------------------------------------------
    def load(self, json_file):
        self.clear()

        try:
            fd = open(json_file)
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

            self._add_data(cat_path=[cat, sub_cat], data={'title':title, 'desc':desc})
            self.examples += 1

        return True

    #-------------------------------------------------------
    '''
    {
        'Курьерские услуги': {
            '__data__': [...],
            'Услуги пешего курьера': {
                '__data__': [...],
                ...
            },
            ...
        }
    }
    '''
    #-------------------------------------------------------
    def _add_data(self, cat_path, data):
        node = self.tree
        for cat in cat_path:
            node[cat] = node.get(cat, {'__data__':[]})
            node = node[cat]
        node['__data__'].append( data )

    #-------------------------------------------------------
    def balance_categories(self):
        pass

    #-------------------------------------------------------
    def get_learn_data(self):
        data = []
        self._recursive_tree2list(self.tree, data)
        return data

    def _recursive_tree2list(self, node, data=[], path=[]):
        for (cat, sub_node) in node.iteritems():
            if cat == '__data__':
                continue

            curr_path = list(path)
            curr_path.append( cat )

            sub_data = sub_node['__data__']
            for d in sub_data:
                data.append( (list(curr_path), d) )

            self._recursive_tree2list(sub_node, data, curr_path)
