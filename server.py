#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import urlparse
import cgi

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer   import ThreadingMixIn

from ml.ml import Analyzer
from ml.query import Query

from ml.utils import logger

kBeautifyJson = True

'''
TODO:
1. чтение конфига
2. биндинг на хосте-порте из конфига
3. вынесение логики обработки гет-пост запросов в ./srv/*.py модули
    - GET:
        - нет параметров:
            * берём форму из srv/template.html, подставляем туда в {%LEARN_DATA%} содержимое файла
              data/learn_data.json
        - get=learn_data - отдаём содержимое файла data/learn_data.json, вставив в него в корень
          поле version с текущей версией
          !=> get=learn_data&version={ver} - отдаём обучающие данные нужной версии.
        - q={query} - отдаём результаты классификатора.
    - POST:
        - если если есть postvars['learn_data'][0], тогда:
            - валидируем его;
            - если всё плохо - ругаемся ошибкой json-парсера;
                { "status": "...error message..." }
            - если всё хорошо:
                * берём последнюю версию из data/learn_data.version (если нет, => 0);
                * переименовываем предыдущую версию data/learn_data.json в learn_data.json.{version}
                * инкремент версии, и добавляем в корень структуры обучающих данных поле 'version'
                  с новой версией.
                * сохраняем в файл data/learn_data.version новую версию.
                * отправляем эти данные на обучение в классификатор.
                * возвращаем статус:
                { "status": "OK" }
'''

#-------------------------------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass
    '''
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
    '''

#-------------------------------------------------------------------------------
class HttpHandler(BaseHTTPRequestHandler):
    def make_resp(self, obj, beautify):
        indent = None if not beautify else 2
        resp = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True )
        resp = resp.encode('utf-8')
        return resp

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        postvars = {}

        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int( self.headers.getheader('content-length') )
            postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)

        self.wfile.write( str(postvars['learn_data'][0]) )

    def do_GET(self):
        pp = urlparse.urlparse( self.path )
        qmap = urlparse.parse_qs( pp.query )

        if len(qmap) == 0:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            with open('srv/template.html') as fd:
                tpl = fd.read()
            self.wfile.write( tpl )
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

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
        log_src_len = len(log_resp)
        kLogLenLimit = 400
        log_resp = log_resp[:kLogLenLimit]
        if len(log_resp) < log_src_len:
            log_resp += '<...>'
        logger.Log( log_resp )

        resp = self.make_resp(obj, beautify=kBeautifyJson)
        self.wfile.write( resp )

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <server.conf>\n"
        sys.exit(1)

    host = '0.0.0.0'
    port = 2222

    config_file = sys.argv[1]

    srv = ThreadedHTTPServer((host, port), HttpHandler)

    '''
    if not srv.init( config_file ):
        sys.exit(1)
    '''

    srv.allow_reuse_address = True
    logger.Log( "Serving on %s:%d... :)" % (host, port) )
    srv.serve_forever()

