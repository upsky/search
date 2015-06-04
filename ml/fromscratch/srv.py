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

        cat_id = self.server.cls.predict( q )

        obj = dict()
        obj['category'] = self.server.cls.cat_id2name( cat_id )

        resp = json.dumps(obj, ensure_ascii=False)
        resp = resp.encode('utf-8')

        self.wfile.write( resp )

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <json_scan_file>\n"
        sys.exit(1)

    json_file = sys.argv[1]

    srv = ThreadedHTTPServer(('0.0.0.0', 2222), HttpHandler)

    srv.load_ml(json_file)

    srv.allow_reuse_address = True
    srv.serve_forever()
