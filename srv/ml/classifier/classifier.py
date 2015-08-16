# -*- coding: utf-8 -*-

#
# Classifier
#

import sys
import json
import pickle

from ..lex import gLexer
from ...logger import Log

from learn_data import LearnDataLoader

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier

kModelFileVersion = '0.1'

#-------------------------------------------------------------------------------
class Classifier:
    def __init__(self, config, load_model=False):
        self.cfg = config
        self.classify_threshold = config['threshold']
        self.model_path = config['model_path']

        self.ldata = LearnDataLoader()
        self.classifier = None
        self.vectorizer = None

        if load_model:
            self.load_model(self.model_path)

    #-------------------------------------------------------
    def learn_from_file(self, learn_file, save_model=False):
        ldata = LearnDataLoader()
        ldata.load(learn_file)
        return self.learn_from_data( ldata, save_model=save_model )

    #-------------------------------------------------------
    def learn_from_str(self, learn_str, save_model=False):
        ldata = LearnDataLoader()
        ldata.loads(learn_str)
        return self.learn_from_data( ldata, save_model=save_model )

    #-------------------------------------------------------
    def learn_from_data(self, learn_data, save_model=False):
        Log("Learning")
        cats_docs = learn_data.get_learn_data()
        Log("Examples to learn: %d" % len(cats_docs))

        Log("Normalizing learning data")
        targets = [x[0] for x in cats_docs]
        docs = [gLexer.normalize_str(x[1]) for x in cats_docs]

        Log("Fitting Vectorizer")
        vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1,2), stop_words=[],
                                     token_pattern=u'(?u)\\b\\w+\\b', smooth_idf=False, norm='l2')
        train_features = vectorizer.fit_transform( docs )
        Log(vectorizer)

        Log("Fitting Classifier")
        classifier = OneVsRestClassifier(
            estimator=SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100,
                                    power_t=0.5, random_state=12, shuffle=False, warm_start=False),
            n_jobs=1
        )
        classifier.fit(train_features, targets)

        self.ldata = learn_data
        self.vectorizer = vectorizer
        self.classifier = classifier

        if save_model:
            self.save_model(self.model_path)

    #-------------------------------------------------------
    def get_categories_tree(self):
        return self.ldata.get_categories_tree()

    #-------------------------------------------------------
    def classify(self, query):
        # классификатор не задан
        if self.vectorizer == None or self.classifier == None:
            query.add_simple_label( 'categories', None )
            return

        # классифаим
        test_features = self.vectorizer.transform( [query.text_normalized] )
        res = self.classifier.predict_proba( test_features )

        # выбираем и сортим, берём топ
        i = 0
        res_arr = []
        for prob in res[0]:
            cat_id = self.classifier.classes_[i]     # преобразуем классы sklearn в наши
            i += 1
            if prob < self.classify_threshold:
                continue
            res_arr.append( (cat_id, prob) )

        res_arr = sorted(res_arr, key=lambda x: x[1], reverse=True)

        # nothing found
        if len(res_arr) == 0:
            query.add_simple_label( 'categories', None )
            return

        for (cat_id, prob) in res_arr:
            cat_path = self.ldata.cat_id2path[cat_id]
            query.add_simple_label( 'categories', {'path':cat_path, 'prob':prob} )

    #-------------------------------------------------------
    def _open_file(self, fname, mode='r'):
        try:
            fd = open(fname, mode)
        except Exception, e:
            raise Exception("Classifier. Can't open file '%s', exc: %s" % (fname, str(e)))
        return fd

    #-------------------------------------------------------
    def save_model(self, model_path):
        with self._open_file( model_path, 'wb+' ) as fd:
            obj = {
                'ver': kModelFileVersion,
                'ldata': self.ldata.dump2obj(),
                'vectorizer': self.vectorizer,
                'classifier': self.classifier
            }
            pickle.dump(obj, fd)

    #-------------------------------------------------------
    def load_model(self, model_path=None):
        if model_path == None:
            model_path = self.model_path

        Log("Loading model from file '%s'" % model_path)

        fd = self._open_file( model_path )

        try:
            obj = pickle.load( fd )
        except Exception, e:
            raise Exception("Classifier. Can't deserialize pickle-model-file '%s', exc: %s" % \
                            (model_file, str(e)))

        ver = obj.get('ver', None)
        if ver != kModelFileVersion:
            raise Exception("Classifier. Different version of model-file or version doesn't present. " \
                            "Expected: %s, given: %s" % \
                            (kModelFileVersion, ver))

        ldata = LearnDataLoader()
        ldata.load_from_obj( obj['ldata'] )

        vectorizer = obj['vectorizer']
        classifier = obj['classifier']

        Log( "vectorizer: " + str(vectorizer) )
        Log( "classifier: " + str(classifier) )

        self.ldata = ldata
        self.vectorizer = vectorizer
        self.classifier = classifier

        Log("Model successfully loaded")
