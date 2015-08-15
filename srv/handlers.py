# -*- coding: utf-8 -*-

import json
from logger import Log

'''
from ml.ml import Analyzer
from ml.query import Query
from ml.utils import logger
'''

#-------------------------------------------------------------------------------
kBeautifyJson = True

#-------------------------------------------------------------------------------
class Handlers:
    def __init__(self, server):
        self.server = server

    #-------------------------------------------------------
    def do_get(self, qmap):
        # no params - response with html-page
        if len(qmap) == 0:
            with open( self.server.cfg['user_form'] ) as fd:
                tpl = fd.read()
            learn_data = self._read_learn_data()
            learn_data = '' if learn_data == None else learn_data

            tpl = tpl.replace('{%LEARN_DATA%}', learn_data, 1)
            return ("text/html; charset=utf-8", tpl)

        content_type = "text/plain; charset=utf-8"

        if 'get' in qmap:
            what = qmap['get']
            what = what[0] if len(what) == 1 else ''
            log_msg = "GET\t" + what

            if what == 'learn_data':
                version = qmap.get('v', None)
                version = version[0] if version != None else None
                learn_data = self._read_learn_data(version)
                if learn_data == None:
                    learn_data = self._resp_status("No such version of learn_data")
                return (content_type, learn_data)

        elif 'q' in qmap:
            return (content_type, "OOOPS. NOT IMPLEMENTED. BUT IT'S COMING SOON!")
            '''
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
        '''

    def _make_resp(self, obj, beautify):
        indent = None if not beautify else 2
        resp = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True)
        resp = resp.encode('utf-8')
        return resp

    #-------------------------------------------------------
    def do_post(self, postvars):
        content_type = "text/plain; charset=utf-8"

        if 'learn_data' in postvars:
            learn_data = postvars['learn_data'][0]

            # - валидируем его; если всё плохо - ругаемся ошибкой json-парсера;
            try:
                ldata = json.loads( learn_data )
            except Exception, e:
                err = "Bad-formed json format, exc: %s" % str(e)
                return (content_type, self._resp_status(err))

            # - если всё хорошо с json'ом, пытаемся обучить, проверив заодно формат структуры
            #  ...

            # - если обучение прошло успешно
            # * берём последнюю версию из data/learn_data.version (если нет, => 0);
            ver = self._read_learn_data_ver()
            # * инкремент версии, и добавляем в корень структуры обучающих данных поле 'version'
            #   с новой версией.
            ver += 1
            ldata['version'] = ver
            # * сохраняем обучающие данные
            with open(self._get_learn_data_file_name(ver), 'wb+') as fd:
                s = json.dumps(ldata, ensure_ascii=False, indent=2)
                fd.write( s.encode('utf8') )

            # * сохраняем в файл data/learn_data.version новую версию.
            self._write_learn_data_ver(ver)

            return (content_type, self._resp_status("OK"))

    def _resp_status(self, err):
        return '{ "status": "%s" }' % err

    #-------------------------------------------------------
    def _read_learn_data_ver(self):
        ver = 0
        try:
            with open( self.server.cfg['learn_data.version'] ) as fd:
                ver = int( fd.read() )
        except:
            pass
        return ver

    def _write_learn_data_ver(self, ver):
        try:
            with open( self.server.cfg['learn_data.version'], 'wb+' ) as fd:
                fd.write( str(ver) )
        except:
            return False
        return True

    def _get_learn_data_file_name(self, ver=None):
        if ver == None:
            ver = str(self._read_learn_data_ver())
        return self.server.cfg['learn_data.file'] + '.' + str(ver)

    def _read_learn_data(self, ver=None):
        try:
            with open( self._get_learn_data_file_name(ver) ) as fd:
                return fd.read()
        except Exception, e:
            Log("Can't read learn data: %s" % str(e))
            return None
