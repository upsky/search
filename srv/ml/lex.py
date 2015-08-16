# -*- coding: utf-8 -*-
#
# Lexer
#

import re
import nltk.stem

#-------------------------------------------------------------------------------
class Token:
    def __init__(self, word, idx, pos_start, pos_end):
        self.word = word
        self.idx = idx
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.word_normalized = word

#-------------------------------------------------------------------------------
class Lexer:
    def __init__(self):
        self.word_split_re = re.compile(r'[\w\-]+', flags=re.UNICODE)
        self.russian_stemmer = nltk.stem.SnowballStemmer('russian')
        self.translate_table = dict( {ord(u'ё'): u'е'} )

    #-------------------------------------------------------
    # Генератор токенов (unicode_words)
    # normalizer - callable method
    # returns: генератор объектов Token
    def tokenize(self, unicode_str, normalizer=None):
        i = 0
        for item in self.word_split_re.finditer(unicode_str):
            w = item.group(0)
            tok = Token(word=w, idx=i, pos_start=item.start(0), pos_end=item.end(0))
            if normalizer:
                tok.word_normalized = normalizer(w)
            yield tok
            i += 1

    #-------------------------------------------------------
    # Возвращает морфологически нормализованное слово:
    # - lowercased, ё -> е, stemmed
    def normalize(self, unicode_word):
        w = unicode_word.lower()
        w = w.translate( self.translate_table ) # ё -> е
        return self.russian_stemmer.stem(w)

    #-------------------------------------------------------
    # Возвращает морфологически нормализованную строку
    # complete_with_spaces - если True, тогда то, что было вырезано стеммером, заполняется пробелами
    def normalize_str(self, unicode_str, complete_with_spaces=False):
        s = u''
        for tok in self.tokenize(unicode_str, normalizer=self.normalize):
            if len(s) > 0:
                s += u' '
            s += tok.word_normalized
            if complete_with_spaces:
                s += (' ' * (len(tok.word) - len(tok.word_normalized)))
        return s

#-------------------------------------------------------------------------------
gLexer = Lexer()
#-------------------------------------------------------------------------------
