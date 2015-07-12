# -*- coding: utf-8 -*-

#
# Classifier
#

import sys
import json
import pickle

from ..lex import gLexer
from ..utils import logger

from learn_data import LearnDataLoader

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier

kModelFileVersion = '2.0'

#-------------------------------------------------------------------------------
class Analyzer:
    def __init__(self, config=None, vectorizer=None, classifier=None, threshold=0.0, return_top=5):
        self.name = 'classifier'
        self.err_msg = None

        if vectorizer != None:
            self.init_vectorizer = vectorizer
        else:
            self.init_vectorizer = CountVectorizer(min_df=1, ngram_range=(1,2))

        if classifier != None:
            self.init_classifier = classifier
        else:
            self.init_classifier = OneVsRestClassifier(
                estimator=SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100,
                                        power_t=0.5, random_state=12, shuffle=False, warm_start=False),
                n_jobs=1
        )

        config_section = self.name
        self.cfg = config.get(config_section, None)

        self.model_file = None
        self.threshold = threshold
        self.return_top = return_top

        if self.cfg != None:
            self.model_file = self.cfg.get('model_file', None)
            self.threshold = self.cfg.get('threshold', threshold)
            self.return_top = self.cfg.get('return_top', return_top)

        if self.model_file == None:
            self.clear()
        else:
            self.load_model( self.model_file )

    #-------------------------------------------------------
    def get_analyzer_name(self):
        return self.name

    #-------------------------------------------------------
    def clear(self):
        self.ldata = LearnDataLoader()
        self.classifier = None
        self.vectorizer = None

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def get_cats_hier(self):
        return self.ldata.get_categories_hier()

    #-------------------------------------------------------
    def analyze(self, query):
        # классифаим
        test_features = self.vectorizer.transform( [query.text_normalized] )
        res = self.classifier.predict_proba( test_features )

        # выбираем и сортим, берём топ
        i = 0
        res_arr = []
        for prob in res[0]:
            cat_id = self.classifier.classes_[i]     # преобразуем классы sklearn в наши
            i += 1
            if prob < self.threshold:
                continue
            res_arr.append( (cat_id, prob) )

        res_arr = sorted(res_arr, key=lambda x: x[1], reverse=True)
        res_arr = res_arr[:self.return_top]

        # nothing found
        if len(res_arr) == 0:
            query.add_simple_label( 'cat', None )
            return True

        for (cat_id, prob) in res_arr:
            cat_path = self.ldata.get_cat_id2path(cat_id)
            query.add_simple_label( 'cat', {'path':cat_path, 'prob':prob} )

        # well done
        return True

    #-------------------------------------------------------
    def is_loaded(self):
        return (self.ldata.is_loaded() != None and self.classifier != None and self.vectorizer != None)

    #-------------------------------------------------------
    def _open_file(self, fname, mode='r'):
        try:
            fd = open(fname, mode)
        except Exception, e:
            self.err_msg = "Error in %s. Can't open file '%s', exc: %s" % (self.name, fname, str(e))
            return None
        return fd

    #-------------------------------------------------------
    def save_model(self, model_file=None):
        if model_file == None:
            model_file = self.model_file
        if model_file == None:
            raise Exception("Error in %s. Specify model file please" % self.name)

        fd = self._open_file( model_file, 'wb+' )
        if fd == None:
            return False

        obj = {
            'ver': kModelFileVersion,
            'ldata': self.ldata.dump2obj(),
            'vectorizer': self.vectorizer,
            'classifier': self.classifier
        }

        pickle.dump(obj, fd)
        fd.close()
        return True

    #-------------------------------------------------------
    def load_model(self, model_file):
        self.clear()

        fd = self._open_file( model_file )
        if fd == None:
            return False

        try:
            obj = pickle.load( fd )
        except Exception, e:
            self.err_msg = "Error in %s. Can't deserialize pickle-model-file '%s', exc: %s" % \
                            (self.name, model_file, str(e))
            return False

        ver = obj.get('ver', None)
        if ver != kModelFileVersion:
            self.err_msg = "Error in %s. Different version of model-file. Expected: %s, given: %s" % \
                            (self.name, kModelFileVersion, ver)
            return False

        self.ldata.load_from_obj( obj['ldata'] )
        self.vectorizer = obj['vectorizer']
        self.classifier = obj['classifier']

        logger.Log( "vectorizer: " + str(self.vectorizer) )
        logger.Log( "classifier: " + str(self.classifier) )

        if not self.is_loaded():
            self.err_msg = "Error in %s. load_model() error. Perhaps model-file is corrupted." % self.name
            return False

        return True

