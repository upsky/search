#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Конвертит прежний формат downloader'ов в удобный формат для обучения.
# По сути заменяет cat + sub_cat на cat_path, который стал массивом из частей,
# составляющий путь к категории.
#

import sys
import os
import re
import json

#-------------------------------------------------
def convert_youdo_com(json_fd):
    n = 0
    for line in json_fd:
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

        cat_path = [cat, sub_cat]
        if cat == sub_cat or len(sub_cat) == 0:
            cat_path = [cat]

        del rec['cat']
        del rec['sub_cat']
        rec['cat_path'] = cat_path

        jstr = json.dumps(rec, ensure_ascii=False)
        print jstr.encode('utf8')

    return True

#-------------------------------------------------
def convert_json2tsv(json_fd):
    n = 0
    for line in json_fd:
        n += 1
        line = line.strip()
        if len(line) == 0:
            continue
        try:
            rec = json.loads( line )
        except Exception, e:
            self.err_msg = "Can't parse json train-example at line %d, exc: %s" % (n, str(e))
            return False

        sss = u"%s\t%s\t%s" % (rec['title'], rec['desc'], '\t'.join(rec['cat_path']))
        print sss.encode('utf-8')

    return True

#-------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  %s MODE\n" % sys.argv[0]
        print >> sys.stderr, "Mode:"
        print >> sys.stderr, ("  youdo_old2new   Convert old youdo.com downloader's format to new (cat+sub_cat -> [cats path])")
        print >> sys.stderr, ("  json2tsv        Convenient for manual-editing (e.g. in Excel). Convert downloaded json-format to\n"
                              "                  tab-separated-values: title TAB desc TAB cat [TAB sub_cat TAB sub_cat TAB ...]")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == 'youdo_old2new':
        res = convert_youdo_com( sys.stdin )
    elif mode == 'json2tsv':
        res = convert_json2tsv( sys.stdin )
    else:
        print >> sys.stderr, "Unknown mode '%s'" % mode
        sys.exit(2)

    sys.exit( int(res == False) )
