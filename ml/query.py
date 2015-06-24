# -*- coding: utf-8 -*-

#
# Лексер запроса: разбирает запрос на токены
#

from utils import logger
import lex

#-------------------------------------------------------------------------------
# Нода дерева запроса
class QNode:
    def __init__(self):
        self.token = None
        self.labels = {}
        self.children = []

#-------------------------------------------------------------------------------
class Query:
    def __init__(self):
        self.text = ''                  # исходный текст запроса в unicode
        self.text_normalized = ''       # исходный текст с нормализованными и стеммированными словами
        self.tokens = []                # список токенов
        self.labels = {}                # метки запроса
        self.tree = None

    def parse(self, utf8_str, stop_words=[]):
        # convert
        try:
            self.text = utf8_str.decode('utf-8')
        except Exception, e:
            logger.Log("Query parser: can't convert your string from utf-8 to unicode. Exc: %s" % str(e))
            return False
        # tokenize
        self.tokens = [tok for tok in lex.gLexer.tokenize(self.text, normalizer=lex.gLexer.stemmed_normalize)]
        self.text_normalized = ' '.join( [tok.word_normalized for tok in self.tokens] )
        return True
