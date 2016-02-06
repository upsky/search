#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import codecs
import re
import nltk.stem

# sys.stdin = codecs.getreader('utf-8')(sys.stdin)
# sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#-----------------------------------------------------------
word_split_re = re.compile(r'[\w\-]+', flags=re.UNICODE)

def split2words(q):
    words = []
    for item in word_split_re.finditer(q):
        w = item.group(0)
        words.append( w )
    return words

#-----------------------------------------------------------
translate_table = dict( {ord(u'ё'): u'е'} )

def normalize_words(words):
    new_words = []
    for w in words:
        w = w.lower()
        w = w.translate( translate_table ) # ё -> е
        new_words.append( w )
    return new_words

#-----------------------------------------------------------
russian_stemmer = nltk.stem.SnowballStemmer('russian')

def norm_morphologically(words):
    new_words = []
    for w in words:
        w = russian_stemmer.stem(w)
        new_words.append( w )
    return new_words

#-----------------------------------------------------------
def norm_phrase(phrase, morph=True):
    words = split2words(phrase)
    words = normalize_words(words)
    if morph:
        words = norm_morphologically(words)
    phrase = u' '.join(words)
    return phrase

#-----------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + " <tabsep_field_num=[0..n)> [--morph]"
        sys.exit(1)

    field_num = int(sys.argv[1])
    do_morph_norm = (len(sys.argv) > 2 and sys.argv[2] == '--morph')

    nnn = 0
    for line in sys.stdin:
        nnn += 1

        fld = line.split('\t')
        if len(fld) <= field_num:
            continue

        try:
            query = fld[field_num]
            # query = query.decode('utf-8')
        except Exception, e:
            print >> sys.stderr, "WARN: line %d, parsing exc: %s" % (nnn, str(e))
            continue

        words = split2words(query)
        words = normalize_words(words)
        if do_morph_norm:
            words = norm_morphologically(words)

        query = ' '.join(words)

        fld_new = fld[0:field_num]
        fld_new.append( query )
        fld_new += fld[field_num+1:]

        s = '\t'.join( fld_new )
        print s
