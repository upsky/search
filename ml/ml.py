# -*- coding: utf-8 -*-

import sys
import json

import query
from utils import logger

import classifier.classifier
import objects.urgency

#-------------------------------------------------------------------------------
class Analyzer:
    def __init__(self, config):
        self.err_msg = None

        self.analyzers = []
        self.analyzers_map = dict()
        self.config = config

        # добавляем анализаторы
        self.add_analyzer( classifier.classifier.Analyzer(self.config) )
        self.add_analyzer( objects.urgency.Analyzer(self.config) )

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def is_ok(self):
        return (self.config != None)

    #-------------------------------------------------------
    def add_analyzer(self, analyzer):
        if analyzer.get_err_msg() != None:
            raise Exception("Error during initializing analyzer '%s', err_msg: %s" %
                            (analyzer.get_analyzer_name(), analyzer.get_err_msg()))

        idx = len(self.analyzers)
        self.analyzers.append( analyzer )
        self.analyzers_map[ analyzer.get_analyzer_name() ] = idx

    #-------------------------------------------------------
    def get_analyzer(self, name):
        idx = self.analyzers_map.get(name, None)
        if idx == None:
            return None
        return self.analyzers[ idx ]

    #-------------------------------------------------------
    # Аналазирует запрос query_obj.
    # Каждый анализатор заполняет query_obj различными метками (query_obj.labels),
    # которые можно далее использовать в качестве результатов анализа.
    # Метками может быть что угодно: определённая категория и её вероятность,
    # найденный в тексте запроса объект и т.п.
    def analyze(self, query_obj):
        for analyzer in self.analyzers:
            if not analyzer.analyze( query_obj ):
                self.err_msg = analyzer.get_err_msg()
                return False

        return True
