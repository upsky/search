#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Берёт tsv-каталог соответствий w2w-каталога и youdo, затем загружает юдушные примеры
# и раскидывает юдушные примеры по нашим категориям.
# После этого пилит задания на N равных пакетов.
#

import sys
import os
import json

if len(sys.argv) < 4:
    print >> sys.stderr, "Usage:\n  " + sys.argv[0] + " <w2w_youdo_catalog.tsv> <learn_data_youdo.json> <N>"
    sys.exit(1)

w2w_youdo_cat = sys.argv[1]
ldata_youdo = sys.argv[2]
nnn = int(sys.argv[3])


#-------------------------------------------------------------------------------
def convert_learn_data(ldata, out_learn_data, path=[]):
    if not type(ldata) is dict:
        raise Exception("Format error, catalog path '%s'. Learn section type must be dict ({})" \
                        % LearnDataLoader.path_arr2str(path))

    ldata_num = 0

    categories = ldata.get('categories', None)
    if categories == None:
        return 0

    for (cat, cat_data) in categories.iteritems():
        cur_path = list(path)
        cur_path.append(cat)

        # если есть обучающие примеры, то их тип должен быть list
        ldata_list = cat_data.get('learn_data', None)
        if ldata_list != None:
            if not type(ldata_list) is list:
                raise Exception("Format error, catalog path: '%s'. Type of 'learn_data' must be array ([])" \
                                % LearnDataLoader.path_arr2str(cur_path))

        str_path = ' -> '.join(cur_path)
        out_learn_data[str_path] = ldata_list
        ldata_num += len(ldata_list)

        ldata_num += convert_learn_data(cat_data, out_learn_data, cur_path)

    return ldata_num


#-------------------------------------------------------------------------------
# строим мапу категорий youdo -> w2w
youdo_2_w2w_map = dict()

w2w_cpath = ''
youdo_cpath = ''
for line in open(w2w_youdo_cat):
    line = line.rstrip('\r\n').decode('utf-8')
    fld = line.split('\t')

    # print ('\t'.join(fld)).encode('utf-8')
    # fld = [f.strip().lower().capitalize() for f in fld]
    # print ('\t'.join(fld)).encode('utf-8')

    w2w_fld = fld[0:2]
    youdo_fld = fld[3:5]

    if len(w2w_fld[0]) == 0 and len(w2w_fld[1]) == 0:
        continue

    w2w_str = ''
    if len(w2w_fld[1]) == 0:
        w2w_cpath = w2w_fld[0]
        w2w_str = w2w_cpath
    else:
        w2w_str = w2w_cpath + ' -> ' + w2w_fld[1]

    if len(youdo_fld[0]) == 0 and len(youdo_fld[1]) == 0:
        print "w2w -/-> youdo: '%s'" % w2w_str.encode('utf-8')
        continue

    youdo_low_paths = []
    if len(youdo_fld[1]) == 0:
        youdo_cpath = youdo_fld[0]
    else:
        youdo_low_paths = youdo_fld[1].split(';')

    if len(youdo_low_paths) == 0:
        youdo_str = youdo_cpath
        youdo_2_w2w_map[youdo_str] = w2w_str
    else:
        for low_path in youdo_low_paths:
            youdo_str = youdo_cpath + ' -> ' + low_path.strip()
            youdo_2_w2w_map[youdo_str] = w2w_str


'''
for (youdo_cat, w2w_cat) in youdo_2_w2w_map.iteritems():
    s = youdo_cat + " ==> " + w2w_cat
    print s.encode('utf-8')

sys.exit(0)
'''
#-------------------------------------------------------------------------------
# загружаем обучаюище примеры
ltree = json.load( open(ldata_youdo) )
converted_ldata = dict()
total_learn_examples = convert_learn_data(ltree, converted_ldata)

#-------------------------------------------------------------------------------
# print total_learn_examples
# раскидываем обучающие примеры
ex_per_packet = total_learn_examples / nnn

print >> sys.stderr, "Examples per packet: %d" % ex_per_packet

packets = [ [] ]
packet_idx = 0
cur_pack_vol = 0

for (youdo_cat, ldata_list) in converted_ldata.iteritems():
    w2w_cat = youdo_2_w2w_map.get(youdo_cat, None)
    if w2w_cat is None:
        continue

    packets[packet_idx].append( w2w_cat )
    for l in ldata_list:
        packets[packet_idx].append( "\t" + l )

    cur_pack_vol += len(ldata_list)
    if cur_pack_vol >= ex_per_packet:
        packets.append( [] )
        packet_idx += 1
        cur_pack_vol = 0

i = 1
for pack in packets:
    print "**************************************************************************************"
    print "*** pack #%d **************************************************************************" % i
    print "**************************************************************************************"
    i += 1
    for ex in pack:
        print ex.encode('utf-8')
    print
    print
    print
