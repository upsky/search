#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Конвертит формат скачанных данных в формат обучения классификатора
#

import sys
import os
import re
import json

#-------------------------------------------------
def recursive_convert_set2list(data_tree):
    children = data_tree.get('categories', None)
    if children == None:
        return

    for (cat, cat_data) in children.iteritems():
        ldata = cat_data.get('learn_data', None)
        if ldata != None and type(ldata) is set:
            ldata = list(ldata)
            cat_data['learn_data'] = ldata

        # идём вглубь
        recursive_convert_set2list(cat_data)

#-------------------------------------------------
def convert_crawled2learndata(json_file):
    ldata = {}
    n = 0
    for line in open(json_file):
        n += 1
        line = line.strip()
        if len(line) == 0:
            continue
        try:
            rec = json.loads( line )
        except Exception, e:
            self.err_msg = "Can't parse json train-example at line %d, exc: %s" % (n, str(e))
            return False

        cat_path = rec.get('cat_path', None)
        if cat_path == None:
            cat = rec['cat']
            sub_cat = rec['sub_cat']
            cat_path = [cat, sub_cat]
            if cat == sub_cat or len(sub_cat) == 0:
                cat_path = [cat]
            del rec['cat']
            del rec['sub_cat']

        rec['cat_path'] = cat_path

        node = ldata
        for c in cat_path:
            node = node.setdefault('categories', {})
            node[c] = node.setdefault(c, {'learn_data': set()})
            node = node[c]

        node['learn_data'].add( rec['title'] )

    # преобразуем все сеты в списки
    recursive_convert_set2list(ldata)

    jstr = json.dumps(ldata, ensure_ascii=False, indent=2)
    print jstr.encode('utf8')

#-------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  %s <crawled_file.json>\n" % sys.argv[0]
        sys.exit(1)

    convert_crawled2learndata(sys.argv[1])
