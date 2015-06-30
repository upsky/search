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
from sklearn.linear_model import SGDClassifier

kModelFileVersion = '1.0'

#-------------------------------------------------------------------------------
class Analyzer:
    def __init__(self, config):
        self.name = 'classifier'
        self.err_msg = None

        config_section = self.name
        self.cfg = config.get(config_section, None)
        if self.cfg == None:
            raise Exception("Can't find config section for analyzer '%s'" % self.name)

        self.model_file = None
        if self.cfg != None:
            self.model_file = self.cfg.get('model_file', None)

        if self.model_file == None:
            self.clear()
        else:
            self.load_model( self.model_file )

    #-------------------------------------------------------
    def get_analyzer_name(self):
        return self.name

    #-------------------------------------------------------
    def clear(self):
        self.cats = {}
        self.cat_id2name = {}
        self.cats_n = 0
        self.cats_hier = {}

        self.classifier = None
        self.vectorizer = None

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def get_cats_hier(self):
        return self.cats_hier

    #-------------------------------------------------------
    def analyze(self, query):
        test_features = self.vectorizer.transform( [query.text_normalized] )
        p = self.classifier.predict(test_features)
        cat_id = p[0]

        cat_info = self._cat_id2info(cat_id)
        query.add_simple_label( 'cat', {'path':cat_info['path'], 'prob':0.99} )
        return True

    #-------------------------------------------------------
    def _cat_id2info(self, id):
        text_path = self.cat_id2name.get(id, None)
        if text_path == None:
            return None
        return self.cats[text_path]

    #-------------------------------------------------------
    def is_loaded(self):
        return (self.cats != None and self.cat_id2name != None and self.cat_n != None and \
                self.cats_hier != None and self.classifier != None and self.vectorizer != None)

    #-------------------------------------------------------
    def train_from_file(self, cats_hier_json, learn_data_json):
        ldata = self._load_train_data( cats_hier_json, learn_data_json )
        if ldata == None:
            return False
        return self.train( ldata.get_learn_data() )

    #-------------------------------------------------------
    def _load_train_data(self, cats_hier_json, learn_data_json):
        logger.Log("Loading training examples...")
        ldata = LearnDataLoader( cats_hier_json, learn_data_json )
        if not ldata.is_ok():
            self.err_msg = "Can't load train data. LearnDataLoader() err: %s" % (ldata.get_err_msg())
            return None

        logger.Log("Balancing training examples in categories tree...")
        ldata.balance_data()

        self.cats_hier = ldata.get_categories_hier()
        return ldata

    #-------------------------------------------------------
    def train(self, learn_data):
        # трансформируем формат LearnDataLoader во внутренний формат
        logger.Log("Normalizing learn-data...")

        docs = []
        targets = []

        for (path, data) in learn_data:
            # save category
            text_path = '_/_'.join(path)

            c = self.cats.get(text_path, None)
            if c == None:
                self.cats_n += 1
                c = {'path':path, 'id':self.cats_n}
                self.cats[text_path] = c
                self.cat_id2name[self.cats_n] = text_path

            document = data['title'] # + ' ' + data['desc']
            document = gLexer.normalize_str( document )
            cat_id = c['id']

            docs.append( document )
            targets.append( cat_id )

        logger.Log("Loaded, docs: %d, its targets: %d" % (len(docs), len(targets)))

        # треним классификатор
        logger.Log("Training classifier...")

        self.vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1,2))
        logger.Log( str(self.vectorizer) )

        self.classifier = SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100,
                                        power_t=0.5, random_state=12, shuffle=False, warm_start=False)
        logger.Log( str(self.classifier) )

        train_features = self.vectorizer.fit_transform( docs )
        self.classifier.fit(train_features, targets)

        logger.Log("Done")
        return True

    #-------------------------------------------------------
    def _open_file(self, fname, mode='r'):
        try:
            fd = open(fname, mode)
        except Exception, e:
            self.err_msg = "Can't open file '%s', exc: %s" % (fname, str(e))
            return None
        return fd

    #-------------------------------------------------------
    def save_model(self, model_file=None):
        if model_file == None:
            model_file = self.model_file
        if model_file == None:
            raise Exception("specify model file please")

        fd = self._open_file( model_file, 'wb+' )
        if fd == None:
            return False

        obj = {
            'ver': kModelFileVersion,
            'cats': self.cats,
            'cat_id2name': self.cat_id2name,
            'cat_n': self.cats_n,
            'cats_hier': self.cats_hier,
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
            self.err_msg = "Can't deserialize pickle-model-file '%s', exc: %s" % (model_file, str(e))
            return False

        ver = obj.get('ver', None)
        if ver != kModelFileVersion:
            self.err_msg = "Error. Different version of model-file. Expected: %s, given: %s" % (kModelFileVersion, ver)
            return False

        self.cats = obj.get('cats', None)
        self.cat_id2name = obj.get('cat_id2name', None)
        self.cat_n = obj.get('cat_n', None)
        self.cats_hier = obj.get('cats_hier', None)
        self.vectorizer = obj.get('vectorizer', None)
        self.classifier = obj.get('classifier', None)

        if not self.is_loaded():
            self.err_msg = "load_model() error. Perhaps model-file is corrupted."
            return False

        return True

