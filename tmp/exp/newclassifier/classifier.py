#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import codecs

import norm
import ngrams
import entities

#-----------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print >> sys.stderr, "Usage:\n  %s <entities.dict> <learn_data.tsv>" % (sys.argv[0])
        sys.exit(1)

    entities_file = sys.argv[1]
    learn_data_file = sys.argv[2]

    sys.stdout = codecs.getwriter('utf8')(sys.stdout)

    entities = entities.Entities(entities_file, basepath='./dicts')
    #entities._print_all(); sys.exit(1)

    nnn = 0
    for line in open(learn_data_file):
        nnn += 1
        line = line.strip().decode('utf-8')
        fld = line.split('\t')
        if len(fld) != 3:
            continue
        (cat, cat_id, text) = fld
        cat_id = int(cat_id)
        norm_text = norm.norm_phrase(text, morph=True)
        ents = entities.get_entities(norm_text, normalize=False)
        ents_str = u'\t'.join( [str(w) + ':' + str(cnt) + ':' + entities.ent_id2name[id] for (id, w, cnt) in ents] )
        s = u'\t'.join( [cat, '', text, ents_str] )
        print s
