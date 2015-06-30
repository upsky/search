#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import urlparse
import json

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer   import ThreadingMixIn

from ml.ml import Analyzer
from ml.query import Query

from ml.utils import logger

kBeautifyJson = True

#-------------------------------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    def init(self, config_file):
        self.config_file = config_file
        try:
            self.ml_config = json.load( open(config_file) )
        except Exception, e:
            logger.Log("Can't load config file '%s'. Exc: %s" % (config_file, str(e)))
            return False
            
        self.analyzer = Analyzer( self.ml_config )
        logger.Log("Loaded analyzer, config file: %s" % config_file)

        return True

#-------------------------------------------------------------------------------
class HttpHandler(BaseHTTPRequestHandler):
    def make_resp(self, obj, beautify):
        indent = None if not beautify else 2
        resp = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True )
        resp = resp.encode('utf-8')
        return resp

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        pp = urlparse.urlparse( self.path )
        qmap = urlparse.parse_qs( pp.query )

        obj = dict()
        log_msg = ''

        if 'get' in qmap:
            what = qmap['get']
            what = what[0] if len(what) == 1 else ''
            log_msg = "GET\t" + what

            if what == 'categories':
                cls = self.server.analyzer.get_analyzer('classifier')
                if cls != None:
                    obj = cls.get_cats_hier()

        elif 'q' in qmap:
            q = qmap.get('q', [])
            q = q[0] if len(q) > 0 else ''

            if len(q) > 3:
                try:
                    q = q.decode('utf-8')
                except Exception, e:
                    logger.Log("Can't decode from utf-8, exc: %s" % str(e))
                    return

                qobj = Query( q )
                self.server.analyzer.analyze( qobj )

                obj = qobj.labels

            try:
                log_msg = 'QUERY\t'
                log_msg += q.encode('utf-8')
            except Exception, e:
                logger.Log("log_msg creating exc: " + str(e))

        log_resp = log_msg + '\t' + self.make_resp(obj, beautify=False)
        logger.Log( log_resp )

        resp = self.make_resp(obj, beautify=kBeautifyJson)
        self.wfile.write( resp )

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <ml.conf>\n"
        sys.exit(1)

    host = '0.0.0.0'
    port = 2222

    config_file = sys.argv[1]

    srv = ThreadedHTTPServer((host, port), HttpHandler)

    if not srv.init( config_file ):
        sys.exit(1)

    srv.allow_reuse_address = True
    logger.Log( "Serving on %s:%d... :)" % (host, port) )
    srv.serve_forever()

