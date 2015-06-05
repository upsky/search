#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import urlparse
import json

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer   import ThreadingMixIn

from testml import Classifier

#-------------------------------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    def load_ml(self, json_file):
        self.cls = Classifier()
        self.cls.train_from_file( json_file )
        print >> sys.stderr, "Trained on %d docs" % self.cls.loaded_docs

#-------------------------------------------------------------------------------
class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        pp = urlparse.urlparse( self.path )
        mq = urlparse.parse_qs( pp.query )
        q = mq.get('q', [])
        q = q[0] if len(q) > 0 else ''

        if len(q) > 3:
            cat_id = self.server.cls.predict( q )
        else:
            cat_id = -1

        obj = dict()
        obj['category'] = self.server.cls.cat_id2name( cat_id )

        try:
            log = 'QUERY\t%s\t%s' % (q, obj['category'].encode('utf-8'))
            print >> sys.stderr, log
        except Exception, e:
            print >> sys.stderr, "Log exc: " + str(e)

        resp = json.dumps(obj, ensure_ascii=False)
        resp = resp.encode('utf-8')

        self.wfile.write( resp )

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <json_scan_file>\n"
        sys.exit(1)

    host = '0.0.0.0'
    port = 2222

    json_file = sys.argv[1]

    srv = ThreadedHTTPServer((host, port), HttpHandler)

    srv.load_ml(json_file)

    srv.allow_reuse_address = True
    print >> sys.stderr, "Serving on %s:%d... :)" % (host, port)
    srv.serve_forever()

