# -*- coding: utf-8 -*-

#
# Объект запроса
#

from lex import gLexer

#-------------------------------------------------------------------------------
class Query:
    def __init__(self, ustr=None, stop_words=[]):
        self.err_msg = None

        if ustr == None:
            self.clear()
        else:
            self.parse(ustr, stop_words)

    #-------------------------------------------------------
    def is_parsed(self):
        return (self.text_normalized != None and len(self.tokens) > 0)

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def clear(self):
        self.text = None                # исходный текст запроса в unicode
        self.text_normalized = None     # исходный текст с нормализованными и стеммированными словами
        self.tokens = []                # список токенов
        self.labels = {}                # метки запроса

    #-------------------------------------------------------
    def add_simple_label(self, name, value):
        self.labels[name] = self.labels.get(name, list())
        self.labels[name].append( value )

    #-------------------------------------------------------
    def add_label(self, section, name, value):
        self.labels[section] = self.labels.get(section, dict())
        self.labels[section][name] = self.labels[section].get(name, list())
        self.labels[section][name].append( value )

    #-------------------------------------------------------
    # Парсит запрос:
    # - на входе - unicode-строка, на выходе True/False;
    # - для случая True - заполненная структура запроса в unicode
    #! TODO : stop_words !!!
    def parse(self, qtext, stop_words=[], complete_with_spaces=True):
        self.clear()
        self.text = unicode(qtext)
        # tokenize
        self.tokens = [tok for tok in gLexer.tokenize(self.text, normalizer=gLexer.normalize)]
        # make normalized text
        self.text_normalized = u''
        for tok in self.tokens:
            if len(self.text_normalized) > 0:
                self.text_normalized += u' '
            self.text_normalized += tok.word_normalized
            if complete_with_spaces:
                self.text_normalized += (' ' * (len(tok.word) - len(tok.word_normalized)))
        return True
