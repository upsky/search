#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Пытаемся выделять ключевые слова из текстов запросов.
#
# Example run:
#   $> python tmp/tagging.py < ml/learn/downloaders/youdo.com/scan_100pages_sorted_uniqed.txt | less
#

'''
Какие идеи приходят после экспериментов:
 1. взять поисковые запросы в большом объеме, взять из них idf, чтобы предлоги и прочая
    шняга отсеилась всё-таки автоматически. (по юдушным запросам мало что отсеивается нормально)
 2. далее по этим idf построить уже на юдушных запросах распределение важности слов.
 ---
 3. выделять в запросе глаголы, т.к. по ним уже явно вырисовывается действие
 4. грамматический анализ. Можно ли без него обойтись, чтобы понять, какие глаголы
    относятся к каким существительным.
'''

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
kNgrams = 1

for (cat_path, title_orig, title_stemmed) in data:
    # сначала юникуем слова
    ng_arr = select_ngrams(title_stemmed, kNgrams)
    ng_set = set( ng_arr )

    # теперь помечаем для каждого, что оно было в одном документе
    for ng in ng_set:
        words[ng] = words.get(ng, 0) + 1

# теперь тэгируем запросы
n_docs = len(data)
import math

for (cat_path, title_orig, title_stemmed) in data:
    stat = {}
    ng_arr = select_ngrams(title_stemmed, kNgrams)
    for ng in ng_arr:
        stat[ng] = words.get(ng, 1000)

    stat_arr = []
    for (w, cnt) in stat.iteritems():
        idf = math.log((float(n_docs) / float(cnt)), 2)
        stat_arr.append( (w, idf) )

    # sort by idf
    stat_arr = sorted(stat_arr, key=lambda x: x[1])

    tags = ''
    stopw = ''
    kStopWordsThreshold = 3.0
    for (ng, idf) in stat_arr:
        if idf >= kStopWordsThreshold:
            if len(tags) > 0: tags += ', '
            tags += "%s=%.03f" % (ng, idf)
        else:
            if len(stopw) > 0: stopw += ', '
            stopw += "%s=%.03f" % (ng, idf)

    sss = "%s\t%s\n\t%s\t(%s)" % (title_orig, cat_path, tags, stopw)
    print sss.encode('utf-8')
