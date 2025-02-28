#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Если у Ubuntu и у тебя нет python2.7 запусти на своём Бубне:
#   sudo apt-get install python2.7
# Затем нужно установить необходимые модули:
#   sudo apt-get install python-nltk \
#                      build-essential python-dev python-setuptools \
#                      python-numpy python-scipy \
#                      libatlas-dev libatlas3gf-base
# Либо просто поставь для питона либы:
#   pip install numpy scipy sklearn
#   pip install nltk
#
# На МакОСи должно сработать вот так (не пробовал; предполагается, что питон2.7 уже стоит):
#   pip install -U numpy scipy scikit-learn nltk
#

import os
import sys
import json
import random

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
# from sklearn import svm

from sklearn import metrics

import nltk.stem

#-------------------------------------------------------------------------------
russian_stemmer = nltk.stem.SnowballStemmer('russian')

class StemmedTfidfVectorizer( TfidfVectorizer ):
    def build_analyzer(self):
        analyzer = super(TfidfVectorizer, self).build_analyzer()
        global russian_stemmer
        return lambda doc: (russian_stemmer.stem(word) for word in analyzer(doc))

#-------------------------------------------------------------------------------
class Classifier:
    def __init__(self):
        self.cats = dict()
        self.n2cat = dict()
        self.cat_n = 0

        self.vectorizer = StemmedTfidfVectorizer(min_df=1, ngram_range=(1,2))
        # self.vectorizer = TfidfVectorizer(min_df=1, analyzer='char', ngram_range=(2,4))
        self.classifier = None
        self.loaded_docs = 0

    #-------------------------------------------------------
    def train_from_file(self, json_file):
        (docs, cats) = self.load_data(json_file)
        self.train(docs, cats)
        self.loaded_docs = len(docs)

    #-------------------------------------------------------
    def load_data(self, json_file):
        docs = list()
        cats = list()

        for line in open(json_file):
            line = line.strip()
            rec = json.loads( line )

            cat_name = rec['cat']
            sub_cat_name = rec['sub_cat']
            title = rec['title']
            desc = rec['desc']

            c = sub_cat_name
            cat_id = self.cats.get(c, None)

            if cat_id == None:
                self.cats[c] = self.cat_n
                self.n2cat[self.cat_n] = c
                cat_id = self.cat_n
                self.cat_n += 1

            docs.append( title )    # desc )
            cats.append( cat_id )

        return (docs, cats)

    #-------------------------------------------------------
    def cat_id2name(self, id):
        return self.n2cat.get(id, '<UNKNOWN>')

    #-------------------------------------------------------
    def train(self, train_docs, train_target):
        print >> sys.stderr, "Learning..."
        train_features = self.vectorizer.fit_transform(train_docs)

        # self.classifier = svm.SVC() # modified_huber | hinge
        # self.classifier = SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, n_iter=5, random_state=42)
        
        #base_dc  = DecisionTreeClassifier(max_depth=1, min_samples_leaf=1)
        #base_sgd = SGDClassifier(loss='modified_huber', penalty='l2', alpha=1e-3, n_iter=5, random_state=42)
        # base_sgd = SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100, power_t=0.5, random_state=12, shuffle=False, warm_start=False)
        # base2_ada = AdaBoostClassifier(base_estimator=base_dc, n_estimators=50, learning_rate=0.5, algorithm="SAMME")
        # self.classifier = AdaBoostClassifier(base_estimator=base2_ada, n_estimators=100, learning_rate=0.5, algorithm="SAMME")

        self.classifier = SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100, power_t=0.5, random_state=12, shuffle=False, warm_start=False)

        print >> sys.stderr, self.classifier

        self.classifier.fit(train_features, train_target)
        print >> sys.stderr, " - done"

    #-------------------------------------------------------
    def predict(self, text):
        test_features = self.vectorizer.transform([text])
        p = self.classifier.predict(test_features)
        return p[0]


#-------------------------------------------------------------------------------
# COMMAND LINE CASE
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    # parse argv
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  %s <scan_json_file> [keyboard|test_self]" % sys.argv[0]
        sys.exit(1)

    json_file = sys.argv[1]
    test_from_keyboard = (len(sys.argv) > 2 and sys.argv[2] == 'keyboard')
    test_self          = (len(sys.argv) > 2 and sys.argv[2] == 'test_self')

    cls = Classifier()
    (docs, cats) = cls.load_data(json_file)
    print >> sys.stderr, "Loaded %d documents" % len(docs)

    # перемешиваем выборку и подготавливаем из неё обучающее и тестовое множества
    data = [(d, c) for (d, c) in zip(docs, cats)]
    random.seed(1)
    random.shuffle( data )

    if test_from_keyboard or test_self:
        train_data = data
        test_data = []
    else:
        r = len(data)*9/10
        train_data = data[:r]
        test_data = data[r:]

    train_docs   = [d for (d,c) in train_data]
    train_target = [c for (d,c) in train_data]
    test_docs   = [d for (d,c) in test_data]
    test_target = [c for (d,c) in test_data]

    cls.train(train_docs, train_target)

    cat_names = [cls.cat_id2name(x) for x in xrange(cls.cat_n)]

    # test
    if test_from_keyboard:
        # predict from keyboard
        print "And now let's predict from keyboard.\nType any query in russian language:"
        while (True):
            line = raw_input()
            cat_id = cls.predict(line)
            print "\t%d=%s" % (cat_id, cls.cat_id2name(cat_id))
    elif test_self:
        predicted = []

        for i in xrange( len(train_docs) ):
            d = train_docs[i]
            t = train_target[i]

            cat_id = cls.predict(d)

            ok = "OK" if t == cat_id else "BAD";
            
            prn = u"%s\t%s\t%s\t%s" % (ok, d, cls.cat_id2name(t), cls.cat_id2name(cat_id))
            print prn.encode('utf-8')

            predicted.append( cat_id )
        
        s = metrics.classification_report(train_target, predicted, target_names=cat_names)
        print >> sys.stderr
        print >> sys.stderr, s.encode('utf-8')
    else:
        # predict from the same collection
        print >> sys.stderr, "Testing..."

        test_predicted = list()

        eq = 0
        for i in xrange( len(test_docs) ):
            d = test_docs[i]
            t = test_target[i]

            print d
            cat_id = cls.predict(d)

            label = "BAD"
            if t == cat_id:
                eq += 1
                label = "OK"

            prn = u"%d\t%s\t'%s'\texpected/predicted: %d=%s / %d=%s" % (i, label, d, t, cls.cat_id2name(t), cat_id, cls.cat_id2name(cat_id))
            print prn.encode('utf-8')

            test_predicted.append( cat_id )

        # show metrics
        s = metrics.classification_report(test_target, test_predicted, target_names=cat_names)
        print
        print s.encode('utf-8')
