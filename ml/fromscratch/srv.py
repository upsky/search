#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer   import ThreadingMixIn


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        # self.path .. to be continued at home ..

        self.wfile.write("my response: %s" % self.path)


if __name__ == '__main__':
    srv = ThreadedHTTPServer(('localhost', 2222), HttpHandler)
    srv.allow_reuse_address = True
    srv.serve_forever()
