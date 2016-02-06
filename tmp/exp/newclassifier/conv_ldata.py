#!/usr/bin/env python
# -*- codign: utf-8 -*-

#
# Конвертит формат обучающего множества.
# Режимы:
# --json2tsv:
#   1. Вытаскивает из обучающего множества формата json все категории и тексты запросов;
#   2. Выводит эти примеры в tsv-формате: category \t category_id \t query
# --tsv2json:
#   Not implemented yet
#

import os
import sys
import codecs
import json

# sys.stdin = codecs.getreader('utf-8')(sys.stdin)
# sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#-----------------------------------------------------------
def recursive_jobj2list(json_obj, out_ldata, cpath=[]):
    if json_obj is None:
        return

    cats = json_obj.get('categories', None)
    if cats is None:
        return

    for (cat, cdata) in cats.iteritems():
        path = list(cpath)
        path.append(cat)
        path_str = ' -> '.join(path)

        cat_id = cdata.get('id', -1)
        ldata = cdata.get('learn_data', None)

        if ldata is not None:
            for lexample in ldata:
                out_ldata.append( (path_str, cat_id, lexample) )

        recursive_jobj2list(cdata, out_ldata, path)

#-----------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + " <mode>"
        print >> sys.stderr, "  --json2tsv  Convert stdin from json-to-tsv format to stdout"
        print >> sys.stderr, "  --tsv2json  Convert stdin from tsv-to-json format to stdout"
        sys.exit(1)

    mode = sys.argv[1]

    if mode == '--json2tsv':
        print >> sys.stderr, "Reading json data from stdin..."
        jstr = ''
        for line in sys.stdin:
            jstr += line

        print >> sys.stderr, "Parsing json data..."
        jobj = json.loads(jstr)

        print >> sys.stderr, "Converting to tsv-format..."
        ldata_list = []
        recursive_jobj2list(jobj, ldata_list)

        print >> sys.stderr, "Outputing"
        for (path_str, cat_id, lexample) in ldata_list:
            s = u'%s\t%d\t%s' % (path_str, cat_id, lexample)
            print s.encode('utf-8')
    elif mode == '--tsv2json':
        print >> sys.stderr, "Not implemented yet. Be the first! :)"
    else:
        print >> sys.stderr, "ERROR: unknown mode '%s'." % mode
        sys.exit(1)

    sys.exit(0)
