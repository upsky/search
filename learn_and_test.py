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

    def __init__(self):
        p = ArgumentParser(prog=sys.argv[0], prefix_chars='-') # , description="Suggests Experiments Client (C) Go.Mail.Ru")

        sp = p.add_subparsers(dest='mode', metavar='mode')

        pm = sp.add_parser('learn_cls', help="Learn classifier")
        self.add_common(pm, show_requires=True)
        pm.add_argument('--hier', required=True, dest='hier', nargs=1, metavar="file.json",
                        help="Categories hierarchy, json")
        pm.add_argument('--data', required=True, dest='data', nargs=1, metavar="file.json",
                        help="Learn data, json")

        pm = sp.add_parser('test', help="Test")
        self.add_common(pm, show_requires=True)

        pm = sp.add_parser('exp', help="Experiments. Tuning classifier and etc mode")
        pm.add_argument('--data', required=True, dest='data', nargs=1, metavar="file.json",
                        help="Learn data, json")

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
args = Args()

mode = getattr(args.p, 'mode')
config_file = getattr(args.p, 'config')

config = json.load( open(config_file) )

if mode == 'learn_cls':
    cats_hier_file = getattr(args.p, 'hier')
    learn_file = getattr(args.p, 'data')

    cls = classifier.Analyzer( config )

    if not cls.train_from_file( cats_hier_file, learn_file ):
        logger.Log("Learn error: %s" % cls.get_err_msg())
        sys.exit(2)

    if not cls.save_model():
        logger.Log("Error, can't save model: %s" % cls.get_err_msg())
        sys.exit(3)

    logger.Log("Model SUCCESSFULLY saved to file '%s'" % cls.model_file)

elif mode == 'experiment':
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import SGDClassifier
    from sklearn import metrics

    cats_hier_file = getattr(args.p, 'hier')
    learn_file = getattr(args.p, 'data')
    cls = classifier.Analyzer(
        vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1,2)),
        classifier = SGDClassifier(loss='modified_huber', penalty='l2',
                                   alpha=5e-4, n_iter=100, power_t=0.5,
                                   random_state=12, shuffle=False, warm_start=False)
    )
    s = metrics.classification_report(train_target, predicted, target_names=cat_names)
    print >> sys.stderr
    print >> sys.stderr, s.encode('utf-8')

elif mode == 'test':
    mktest_file = getattr(args.p, '')
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
else:
    print >> sys.stderr, "ERROR: unknown mode %s" % mode

sys.exit(0)
