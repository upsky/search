# -*- coding: utf-8 -*-

import sys
import json

from ml.utils import logger

from ml.query import Query
from ml import Analyzer
from ml.classifier import classifier

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
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print >> sys.stderr, "ERROR\nUsage:\n  " + sys.argv[0] + " <MODE> <config_file.json> ...opts..."
        print >> sys.stderr, "MODE:\n" \
                             "  learn opts: <categories_hier.json> <learn_data.json>\n" \
                             "  test  opts: <model_path> <marker_test.json>\n"
        sys.exit(1)

    mode = sys.argv[1]
    config_file = sys.argv[2]

    config = json.load( open(config_file) )

    if mode == 'learn':
        cats_hier_file = sys.argv[3]
        learn_file = sys.argv[4]

        cls = classifier.Analyzer( config )

        if not cls.train_from_file( cats_hier_file, learn_file ):
            logger.Log("Learn error: %s" % cls.get_err_msg())
            sys.exit(2)

        if not cls.save_model():
            logger.Log("Error, can't save model: %s" % cls.get_err_msg())
            sys.exit(3)

        logger.Log("Model SUCCESSFULLY saved to file '%s'" % cls.model_file)

    elif mode == 'test':
        mktest_file = sys.argv[4]
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
