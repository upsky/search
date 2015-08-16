# -*- coding: utf-8 -*-

import sys
import json

from ..logger import Log
from query import Query

from classifier.classifier import Classifier
import objects.urgency

#-------------------------------------------------------------------------------
class Analyzer:
    def __init__(self, config):
        self.err_msg = ''
        self.init_ok = True

        self.cfg = config
        self.classifier = Classifier( self.cfg['classifier'] )

        # try load model
        try:
            self.classifier.load_model()
        except Exception, e:
            self.init_ok = False
            self.err_msg = "Can't initialize classifier, exc: %s" % str(e)

    def learn_classifier(self, learn_data):
        cls = Classifier( self.cfg['classifier'] )
        cls.learn_from_data(learn_data, save_model=True)
        self.classifier = cls

    def analyze(self, query):
        return self.classifier.classify( query )
