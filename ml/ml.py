# -*- coding: utf-8 -*-

import sys

import query
import utils

#-------------------------------------------------------------------------------
class Analyzer:
    def __init__(self):
        pass

    def analyze(self, utf8_text):
        q = query.Query()
        if not q.parse(utf8_text):
            return False
        print "text: " + q.text.encode(utils.kScreenEncoding)
        print "text_normalized: " + q.text_normalized.encode(utils.kScreenEncoding)
        for tok in q.tokens:
            print "\t%d. %s (%s), (%d, %d)" % \
                  (tok.idx, tok.word.encode(utils.kScreenEncoding), tok.word_normalized.encode(utils.kScreenEncoding), \
                   tok.pos_start, tok.pos_end)
        print
        return True

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    a = Analyzer()
    for line in sys.stdin:
        a.analyze(line)
