#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import nltk.stem



#-------------------------------------------------------
def select_ngrams(s, ngrams):
    res = []

    warr = s.split()
    for i in xrange( len(warr) ):
        r_range = min(i + ngrams, len(warr))

        for n in xrange(i, r_range):
            ngram = ' '.join( warr[i:n+1] )
            res.append( ngram )

    return res

russian_stemmer = nltk.stem.SnowballStemmer('russian')

#-------------------------------------------------------
def load(json_fd):
    data = []
    n = 0
    for line in json_fd:
        n += 1
        line = line.strip()
        if len(line) == 0:
            continue
        try:
            rec = json.loads( line )
        except Exception, e:
            print >> sys.stderr, "Can't parse json train-example at line %d, exc: %s" % (n, str(e))
            return None

        cat_path = '/'.join( rec['cat_path'] )
        title_orig = rec['title'].lower()
        title_stemmed = ' '.join( [russian_stemmer.stem(w) for w in title_orig.split()] )

        data.append( (cat_path, title_orig, title_stemmed) )

    return data

'''
Идея сейчас жутко простая:
    - чем в меньшем количестве документов встретилось конкретное слово, тем больше оно характеризует этот документ
    - т.е. это по сути тот же idf.
'''


#-------------------------------------------------------
# собираем статистику
data = load( sys.stdin )
if data == None:
    sys.exit(1)

words = {}
kNgrams = 2

for (cat_path, title_orig, title_stemmed) in data:
    # сначала юникуем слова
    ng_arr = select_ngrams(title_stemmed, kNgrams)
    ng_set = set( ng_arr )

    # теперь помечаем для каждого, что оно было в одном документе
    for ng in ng_set:
        words[ng] = words.get(ng, 0) + 1

# теперь тэгируем запросы
for (cat_path, title_orig, title_stemmed) in data:
    stat = {}
    ng_arr = select_ngrams(title_stemmed, kNgrams)
    for ng in ng_arr:
        stat[ng] = words.get(ng, 1000)

    stat_arr = [(w, cnt) for (w, cnt) in stat.iteritems()]
    stat_arr = sorted(stat_arr, key=lambda x: x[1])

    tags = ''
    for (ng, cnt) in stat_arr:
        if len(tags) > 0: tags += ', '
        tags += "%s=%d" % (ng, cnt)

    sss = "%s\t%s\t%s" % (title_orig, tags, cat_path)
    print sss.encode('utf-8')
