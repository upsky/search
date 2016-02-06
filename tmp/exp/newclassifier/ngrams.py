#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

# import codecs
# sys.stdin = codecs.getreader('utf-8')(sys.stdin)
# sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#-----------------------------------------------------------
# Выделяем все нграммы длиной от 1 до n слов.
# strex     intput string to make ngrams on;
# n         number of maximum length of ngrams (in words);
# ngrams    in-out: in=dict(), out={ngram_str: counter}
def split2ngrams(strex, n, ngrams):
    wlist = strex.split()
    wnum = len(wlist)
    for i in xrange(wnum):
        for j in xrange(n):
            if (i + j) < wnum:
                ng_list = wlist[i:i+j+1]
                ng_str = u' '.join(ng_list)
                ngrams[ng_str] = ngrams.get(ng_str, 0) + 1

#-----------------------------------------------------------
def ng_dict2sortedlist(ng_dict):
    ng_list = [ (ng, cnt) for (ng, cnt) in ng_dict.iteritems() ]
    ng_list = sorted(ng_list, key=lambda x: x[1], reverse=True)
    return ng_list

#-----------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: " + sys.argv[0] + " <N> [<mode>=(--plain|--group2cats)]"
        sys.exit(1)

    N = int(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else '--plain'

    if mode != '--plain' and mode != '--group2cats':
        print >> sys.stderr, "ERROR: unknown mode '%s'" % mode
        sys.exit(2)

    print >> sys.stderr, "Parsing queries and splitting them to ngrams..."
    ngrams = {}
    for line in sys.stdin:
        fld = line.split('\t')
        if len(fld) != 3:
            continue

        (cat, cat_id, query) = fld

        if mode == '--plain':
            split2ngrams(query, N, ngrams)
        elif mode == '--group2cats':
            ngrams[cat] = ngrams.get(cat, {})
            split2ngrams(query, N, ngrams[cat])

    print >> sys.stderr, "Outputing"
    if mode == '--plain':
        ng_list = ng_dict2sortedlist(ngrams)
        for (ng, cnt) in ng_list:
            print '%s\t%d' % (ng, cnt)
    elif mode == '--group2cats':
        for (cat, ng_dict) in ngrams.iteritems():
            print cat
            ng_list = ng_dict2sortedlist(ng_dict)
            for (ng, cnt) in ng_list:
                print '\t%s\t%d' % (ng, cnt)

    sys.exit(0)
