#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import urlparse
import cgi

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer   import ThreadingMixIn

from srv import utils, config, logger, handlers

'''
TODO:
[+1]. чтение конфига
[+2]. биндинг на хосте-порте из конфига
3. вынесение логики обработки гет-пост запросов в ./srv/*.py модули
    + GET:
        + нет параметров:
            * берём форму из srv/template.html, подставляем туда в {%LEARN_DATA%} содержимое файла
              data/learn_data.json
        + get=learn_data - отдаём содержимое файла data/learn_data.json, вставив в него в корень
          поле version с текущей версией
          !=> get=learn_data&version={ver} - отдаём обучающие данные нужной версии.
        - q={query} - отдаём результаты классификатора.
    + POST:
        - если если есть postvars['learn_data'][0], тогда:
            + валидируем его;
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
    def init(self, cfg):
        self.cfg = cfg
        self.handlers = handlers.Handlers(self)

        ''' self.analyzer = Analyzer( self.ml_config )
        logger.Log("Loaded analyzer, config file: %s" % config_file)'''

        return True

#-------------------------------------------------------------------------------
class HttpHandler(BaseHTTPRequestHandler):
    #-------------------------------------------------------
    def do_GET(self):
        # parse params
        purl = urlparse.urlparse( self.path )
        qmap = urlparse.parse_qs( purl.query )

        # handle
        res = self.server.handlers.do_get(qmap)
        if res == None:
            return

        (content_type, content) = res

        # send response
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()

        self.wfile.write( content )

    #-------------------------------------------------------
    def do_POST(self):
        postvars = {}

        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int( self.headers.getheader('content-length') )
            postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)

        res = self.server.handlers.do_post(postvars)
        if res == None:
            return

        (content_type, content) = res

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()

        self.wfile.write( content )

#-------------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage:\n  " + sys.argv[0] + "  <server.conf>\n"
        return 1

    config_file = sys.argv[1]
    cfg = config.Config(config_file)
    if not cfg.is_loaded():
        return 2

    srv = ThreadedHTTPServer((cfg['host'], cfg['port']), HttpHandler)

    if not srv.init( cfg ):
        return 3

    srv.allow_reuse_address = True
    logger.Log( "Serving on %s:%d... :)" % (cfg['host'], cfg['port']) )
    srv.serve_forever()

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit( main() )
