# -*- coding: utf-8 -*-
#
# Test and Learn
#

import sys
import json
from argparse import ArgumentParser


from ml.utils import logger

from ml.query import Query
from ml import Analyzer
from ml.classifier import classifier

#-------------------------------------------------------------------------------
# parse commandline arguments
class Args:
    def add_common(self, group, show_requires):
        group.add_argument('-c', '--config', required=True, dest='config', nargs=1, metavar="config.json",
                           help="ML config file")

    def add_classifier_learn(self, group, show_requires):
        group.add_argument('--hier', required=True, dest='hier', nargs=1, metavar="cats_hierarhcy.json",
                           help="Categories hierarchy, json")
        group.add_argument('--data', required=True, dest='data', nargs=1, metavar="learn_data.json",
                           help="Learn data, json")

    def __init__(self):
        p = ArgumentParser(prog=sys.argv[0], prefix_chars='-') # , description="...")

        sp = p.add_subparsers(dest='mode', metavar='mode')

        pm = sp.add_parser('learn_cls', help="Learn classifier")
        self.add_common(pm, show_requires=True)
        self.add_classifier_learn(pm, show_requires=True)

        pm = sp.add_parser('test', help="Test")
        self.add_common(pm, show_requires=True)
        pm.add_argument('-t', '--test', required=True, dest='test_file', nargs=1, metavar="marker_test.json",
                        help="Json-file with marker_test")

        pm = sp.add_parser('exp', help="Experiments. Tuning classifier and etc mode")
        self.add_classifier_learn(pm, show_requires=True)
        pm.add_argument('--key', required=True, dest='key', nargs=1, metavar="key",
                        help="Well, some key for experiments")

        pm = sp.add_parser('exp_vect', help="Experiments. Tuning vectorizer and etc mode")
        self.add_classifier_learn(pm, show_requires=True)
        pm.add_argument('--key', required=True, dest='key', nargs=1, metavar="key",
                        help="Well, some magical key for experiments")

        if len(sys.argv) > 1 and (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
            print >> sys.stderr, "\nType\n  %s <mode> --help\nto get help about concrete mode\n" % sys.argv[0]

        self.p = p.parse_args()

#-------------------------------------------------------------------------------
def recursive_test(test, res, path=[]):
    for (name, test_val) in test.iteritems():
        path.append( name )

        res_val = res.get(name, None)

        # такой подсекции/значения по тесту НЕ должно быть
        if test_val == None and res_val == None:
            return True

        if not type(test_val) is type(res_val):
            return False

        if type(test_val) is dict:                                  # dict
            if not recursive_test( test_val, res_val, path ):
                return False
        elif type(test_val) is list or type(test_val) is tuple:     # list or tuple
            if len(test_val) > len(res_val):                        # len of test must be <= len of result
                return False
            i = 0
            for i in xrange(len(test_val)):
                if not recursive_test( test_val[i], res_val[i], path ):
                    return False
                i += 1
        else:                                                       # str, number, boolean
            if test_val != res_val:
                return False

    return True

#-------------------------------------------------------------------------------
def max_except_this(lst, except_idx):
    if len(lst) < 2:
        return None

    m = None
    if except_idx == 0:
        m = lst[1]
    else:
        m = lst[0]

    for i in xrange(len(lst)):
        if i == except_idx:
            continue
        v = lst[i]
        m = max(m, v)

    return m

#-------------------------------------------------------------------------------
args = Args()

mode = getattr(args.p, 'mode')

if mode == 'learn_cls':
    config_file = getattr(args.p, 'config')[0]

    cats_hier_file = getattr(args.p, 'hier')[0]
    learn_file = getattr(args.p, 'data')[0]

    cls = classifier.Analyzer( config )

    if not cls.train_from_file( cats_hier_file, learn_file ):
        logger.Log("Learn error: %s" % cls.get_err_msg())
        sys.exit(2)

    if not cls.save_model():
        logger.Log("Error, can't save model: %s" % cls.get_err_msg())
        sys.exit(3)

    logger.Log("Model SUCCESSFULLY saved to file '%s'" % cls.model_file)

elif mode == 'test':
    config_file = getattr(args.p, 'config')[0]
    mktest_file = getattr(args.p, 'test_file')[0]

    a = Analyzer( config )

    mk = json.load( open(mktest_file) )
    for test in mk:
        print >> sys.stderr, "Test:'%s', query:'%s', expected:'%s'" % (test['name'], test['query'], str(test['res']))

        qobj = Query( test['query'] )
        if not qobj.is_parsed():
            logger.Log("Query parser error: %s" % qobj.get_err_msg())
            sys.exit(2)

        if not a.analyze( qobj ):
            logger.Log("Error during analyzing, error message: %s" % a.get_err_msg())
            sys.exit(2)

        print >> sys.stderr, " = query labels: " + str(qobj.labels)

        # рекурсивно проверяем результат:
        # ищем в рузультатах анализатора только то, что указано для поиска в тесте
        test_res = test['res']
        test_path = []
        if not recursive_test(test_res, qobj.labels, test_path):
            p = '.'.join( test_path )
            logger.Log("Test FAILED. Test path: '%s'" % p)
            sys.exit(3)

        print >> sys.stderr, " + OK"

    print >> sys.stderr, "[+] All tests SUCCESSFULLY done"

elif mode == 'exp_vect':
    from ml.classifier.learn_data import LearnDataLoader
    from ml.lex import Lexer

    from sklearn.linear_model import SGDClassifier
    from sklearn.multiclass import OneVsRestClassifier

    from sklearn.cross_validation import cross_val_score

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.feature_extraction.text import CountVectorizer

    cats_hier_file = getattr(args.p, 'hier')[0]
    learn_file = getattr(args.p, 'data')[0]
    exp_key = getattr(args.p, 'key')[0].split(',')

    lexer = Lexer()
    vectorizer = None
    classifier = None
    ldata = LearnDataLoader()

    # load learn data
    if not ldata.load(cats_hier_file, learn_file, balance_category_min=10, log=True):
        print >> sys.stderr, "Error: " + ldata.get_err_msg()
        sys.exit(1)

    cats_docs = ldata.get_learn_data(fields_to_get=['title'])
    logger.Log("Examples to learn: %d" % len(cats_docs))

    logger.Log("Normalizing learning data")
    kSelCatId = 3

    docs = [x[1] for x in cats_docs]

    train_docs = [lexer.normalize_str(x[1], complete_with_spaces=False) for x in cats_docs]
    # train_targets = [int(x[0] == kSelCatId) for x in cats_docs]
    train_targets = [x[0] for x in cats_docs]

    if 'vec_only_cat' in exp_key:
        vect_docs = [lexer.normalize_str(x[1], complete_with_spaces=False) for x in cats_docs if x[0] == kSelCatId]
    else:
        vect_docs = train_docs

    # docs = [x[1] for x in cats_docs if x[0] == kSelCatId]
    # docs = [ u'Курьер на три доставки от во от Новогиреево', u'Курьер на Экспедитор во Фрязино' ]
    # docs = [ u'aaa bbb figam ccc zzz', u'aaa bbb some ccc zzz' ]

    # use_idf = False  ==  CountVectorizer()
    #vectorizer = TfidfVectorizer(min_df=1, encoding=u'utf8', ngram_range=(1,2), token_pattern=u'(?u)\\b\\w+\\b',
    #                             stop_words=[], smooth_idf=False, norm=None, use_idf=False)
    vectorizer = CountVectorizer(ngram_range=(1,2))
    print vectorizer

    vectorizer.fit( vect_docs )
    train_features = vectorizer.transform( train_docs )

    if 'cls_ensemble' in exp_key:
        classifier = OneVsRestClassifier(
            estimator=SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100,
                                    power_t=0.5, random_state=12, shuffle=False, warm_start=False),
            n_jobs=1
        )
    else:
        classifier = SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100,
                                   power_t=0.5, random_state=12, shuffle=False, warm_start=False)

    logger.Log(classifier)

    logger.Log("Fitting Classifier")
    classifier.fit(train_features, train_targets)

    # print "Aiming category: %s" % ('/'.join( ldata.get_cat_id2path(kSelCatId) )).encode('utf-8')

    # считаем отступы для всех документов нашей категории
    if 'margins' in exp_key:
        test_cats_docs = ldata.get_learn_data(fields_to_get=['title'])
        test_docs = [x[1] for x in test_cats_docs]
        test_norm_docs = [lexer.normalize_str(x[1], complete_with_spaces=False) for x in test_cats_docs]

        margins = [0] * len(train_docs)

        for i in xrange(len(train_docs)):
            d = test_norm_docs[i]
            target = train_targets[i]

            f = vectorizer.transform( [d] )
            res = classifier.predict_proba(f)[0]

            # здесь у нас всего два класса: целевой (1) и НЕ-класс (0), поэтому всё упрощается
            margins[i] = res[1] - res[0]

            learn_cat = ('/'.join( ldata.get_cat_id2path(cats_docs[i][0]) )).encode('utf-8')
            # print "%s\t%s\t%.02f" % (learn_cat, test_docs[i].encode('utf-8'), margins[i])

        # убираем документы, для которых отступ оказался порога в НЕ-класс.
        kMarginThreshold = 0.05
        for i in xrange(len(margins)):
            if margins[i] < kMarginThreshold:
                train_targets[i] = 0

    if 'kfolds' in exp_key:
        print cross_val_score(classifier, train_features, train_targets, cv=3)

    '''
    voc = [ (w, c) for (w, c) in vectorizer.vocabulary_.iteritems() ]
    voc = sorted(voc, key=lambda x: x[1])

    print train_features.indices
    print train_features.indptr
    print train_features.data

    rows = len(train_features.indptr) - 1
    # rows
    for r in xrange(rows):
        r_from = train_features.indptr[r]
        r_to = train_features.indptr[r+1]
        print "doc %d" % r
        # columns
        for c in train_features.indices[ r_from:r_to ]:
            word_id = c
            print "\t%s\t%.02f" % (voc[word_id][0], train_features.data[word_id])
    '''

elif mode == 'exp':
    from ml.classifier.learn_data import LearnDataLoader
    from ml.lex import Lexer

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import SGDClassifier
    import sklearn
    import sklearn.neighbors
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.lda import LDA
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.svm import SVC
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.multiclass import OutputCodeClassifier
    from sklearn.svm import LinearSVC
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn import metrics
    from sklearn.cross_validation import cross_val_score
    import nltk
    import pickle

    from ml.objects import urgency

    cats_hier_file = getattr(args.p, 'hier')[0]
    learn_file = getattr(args.p, 'data')[0]
    exp_key = getattr(args.p, 'key')[0].split(',')

    lexer = Lexer()
    vectorizer = None
    classifier = None
    ldata = LearnDataLoader()

    '''
    TODO:
    1. прикрутить pipeline с подбором параметров
    2. прикрутить стоп-слова
    3. skip invalid learning examples (with wrong class) while loading them.
    4. стоп-слова из urgency; max_df=[0.7; 1)
    '''

    if 'fit' in exp_key:
        # classifier = sklearn.neighbors.KNeighborsClassifier(n_neighbors=10, weights='distance')
        # classifier = sklearn.naive_bayes.MultinomialNB()
        classifier = OneVsRestClassifier(
            estimator=SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100,
                                    power_t=0.5, random_state=12, shuffle=False, warm_start=False),
            n_jobs=1
        )
        # classifier = SGDClassifier(loss='modified_huber', penalty='l2', alpha=5e-4, n_iter=100, power_t=0.5, random_state=12, shuffle=False, warm_start=False)

        # classifier = sklearn.lda.LDA() # not enough memory
        # classifier = DecisionTreeClassifier(random_state=0)
        # classifier = LogisticRegression(multi_class='multinomial', solver='newton-cg')
        # classifier = GradientBoostingClassifier(n_estimators=300, max_depth=25, warm_start=True)
        # classifier = OutputCodeClassifier(LinearSVC(random_state=0), code_size=2, random_state=0, n_jobs=2)

        # load learn data
        if not ldata.load(cats_hier_file, learn_file, balance_category_min=20, log=True):
            print >> sys.stderr, "Error: " + ldata.get_err_msg()
            sys.exit(1)

        cats_docs = ldata.get_learn_data()
        logger.Log("Examples to learn: %d" % len(cats_docs))

        logger.Log("Normalizing learning data")
        targets = [x[0] for x in cats_docs]
        docs = [lexer.normalize_str(x[1], complete_with_spaces=False) for x in cats_docs]

        logger.Log("Preparing stop-words")
        stop_words = set()
        for phrase in urgency.kVocab:
            for tok in lexer.tokenize( phrase.decode('utf-8') ):
                stop_words.add( tok.word_normalized )
        stop_words = list(stop_words)

        logger.Log("Fitting Vectorizer")
        vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1,2), stop_words=stop_words,
                                     token_pattern=u'(?u)\\b\\w+\\b', smooth_idf=False, norm='l2')
        train_features = vectorizer.fit_transform( docs )
        logger.Log(vectorizer)

        logger.Log("Fitting Classifier")
        classifier.fit(train_features, targets)

        logger.Log("classifier classes: %d" % len(classifier.classes_))

        logger.Log("Saving")
        fd = open('test_model.pkl', 'wb+')
        obj = {
            'ver': "2.0",
            'classifier': classifier,
            'vectorizer': vectorizer,
            'ldata': ldata.dump2obj()
        }
        pickle.dump(obj, fd)
        fd.close()
        logger.Log("done")

    else:
        logger.Log("Loading model")
        fd = open('test_model.pkl')
        obj = pickle.load( fd )
        fd.close()
        classifier = obj['classifier']
        vectorizer = obj['vectorizer']
        ldata.load_from_obj( obj['ldata'] )

    our_cats_ids = ldata.get_cats_ids_list()
    logger.Log("Number of our classes: %d" % len(our_cats_ids))
    logger.Log("classifier classes: %s" % str(classifier.classes_))

    # calculate margin for learning examples
    if 'margin' in exp_key:
        cats_docs = ldata.get_learn_data()
        logger.Log("Examples to sift: %d" % len(cats_docs))

        example_idx = 0

        for (cat_id, text) in cats_docs:
            example_idx += 1
            if example_idx % 100 == 0:
                sys.stderr.write('\r%d' % example_idx)

            norm_text = lexer.normalize_str(text)
            f = vectorizer.transform( [norm_text] )

            '''
            res_cat_id = classifier.predict(f)
            if res_cat_id == cat_id:
                c = ldata.get_cat_id2path(cat_id)
                cat = c[0]
                if len(c) > 1:
                    sub_cat = c[1]
                else:
                    sub_cat = c[0]
                out = {
                    'cat': cat,
                    'sub_cat': sub_cat,
                    'title': text,
                    'desc': ''
                }
                sss = json.dumps( out, ensure_ascii=False, indent=None, sort_keys=True )
                print sss.encode('utf-8')
            continue
            '''

            res = classifier.predict_proba(f)[0]

            # преобразуем классы sklearn к нашим классам
            our_res = [0.0] * len(our_cats_ids)
            for i in xrange(len(res)):
                our_cat_idx = classifier.classes_[i] - 1
                our_res[ our_cat_idx ] = res[i]

            gamma_true = our_res[cat_id-1]
            gamma_other_max = max_except_this(our_res, cat_id-1)

            margin = gamma_true - gamma_other_max
            sss = u"%d\t%d\t%s\t%s\t%.07f\tgamma_true:%.07f\tgother_max:%.07f" % \
                   (example_idx, cat_id, ('/'.join(ldata.get_cat_id2path(cat_id))), text, margin, \
                    gamma_true, gamma_other_max)
            print sss.encode('utf-8')

        sys.exit(0)

    if 'kfolds' in exp_key:
        print cross_val_score(classifier, train_features, targets, cv=10)
    else:
        logger.Log("Predicting")
        # predict
        while (True):
            line = raw_input('type>>> ')
            line = line.decode('cp866')
            line = lexer.normalize_str(line)

            print line.encode('cp866')

            f = vectorizer.transform( [line] )

            if 'one' in exp_key:
                res = classifier.predict( f )
                cat_id = res[0]
                print cat_id
                prob = 1.0
                print "cat_id=%d, prob=%03f, '%s'" % (cat_id, prob, ('/'.join(ldata.get_cat_id2path(cat_id)).encode('cp866')))
            else:
                res = classifier.predict_proba( f )
                # выбираем и сортим
                kThreshold = 0.0 #51
                i = 0
                res_arr = []
                for prob in res[0]:
                    cat_id = classifier.classes_[i]     # преобразуем классы sklearn в наши
                    i += 1
                    if prob < kThreshold:
                        continue
                    res_arr.append( (cat_id, prob) )

                res_arr = sorted(res_arr, key=lambda x: x[1], reverse=True)

                if len(res_arr) == 0:
                    print "Nothing found"

                i = 0
                while i < 5 and i < len(res_arr):
                    (cat_id, prob) = res_arr[i]
                    print "cat_id=%d, prob=%.3f, '%s'" % (cat_id, prob, ('/'.join(ldata.get_cat_id2path(cat_id)).encode('cp866')))
                    i += 1

    # cross validation
    # from sklearn.cross_validation import cross_val_score
    # cross_val_score(clf, iris.data, iris.target, cv=10)

    # s = metrics.classification_report(train_target, predicted, target_names=cat_names)
    # print >> sys.stderr
    # print >> sys.stderr, s.encode('utf-8')

else:
    print >> sys.stderr, "ERROR: unknown mode %s" % mode

sys.exit(0)
