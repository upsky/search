# -*- coding: utf-8 -*-

import json
import traceback

from logger import Log

from ml.analyzer import Analyzer
from ml.classifier.learn_data import LearnDataLoader
from ml.query import Query

#-------------------------------------------------------------------------------
kBeautifyJson = True

#-------------------------------------------------------------------------------
class Handlers:
    #-------------------------------------------------------
    def __init__(self, config, server):
        self.cfg = config
        self.server = server
        self.analyzer = Analyzer( self.cfg['analyzer'] )
        if not self.analyzer.init_ok:
            Log("WARNING: Can't init analyzer, err: %s" % self.analyzer.err_msg)

    #-------------------------------------------------------
    def do_get(self, qmap):
        # no params - response with html-page
        if len(qmap) == 0:
            with open( self.cfg['user_form'] ) as fd:
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
            elif what == 'categories':
                cats_tree = self.analyzer.classifier.get_categories_tree()
                s = json.dumps( cats_tree, ensure_ascii=False, indent=2 )
                s = s.encode('utf8')
                return (content_type, s)

        elif 'q' in qmap:
            q = qmap.get('q', [])
            q = q[0] if len(q) > 0 else ''

            if len(q) < 3:
                return (content_type, '{}')

            try:
                q = q.decode('utf-8')
            except Exception, e:
                raise Exception("Can't decode from utf-8, exc: %s" % str(e))

            qobj = Query( q )
            self.analyzer.analyze( qobj )

            obj = qobj.labels

            # log query and analyzer's response
            log_resp = q.encode('utf8') + '\t' + self._make_resp(obj, beautify=False)
            log_src_len = len(log_resp)
            kLogLenLimit = 400
            log_resp = log_resp[:kLogLenLimit]
            if len(log_resp) < log_src_len:
                log_resp += '<...>'
            Log( log_resp )

            resp = self._make_resp(obj, beautify=kBeautifyJson)
            return (content_type, resp)

    def _make_resp(self, obj, beautify):
        indent = None if not beautify else 2
        resp = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True)
        resp = resp.encode('utf-8')
        return resp

    #-------------------------------------------------------
    def do_post(self, postvars):
        content_type = "text/plain; charset=utf-8"

        if 'learn_data' in postvars:
            learn_str = postvars['learn_data'][0]

            # лочимся, чтобы не было конкурентных перезаписей
            lock_file = self.cfg['learn_data.version'] + '.lock'
            lock_fd = open(lock_file, 'a+')
            try:
                flock.lock(lock_fd, flock.LOCK_EX)
            except:
                pass

            ldata = LearnDataLoader()
            # - пытаемся обучить, проверив заодно формат структуры
            try:
                ldata.loads( learn_str )
                self.analyzer.learn_classifier( ldata )
            except Exception, e:
                traceback.print_exc()
                Log("Error during learning, exc: %s" % str(e))
                return (content_type, self._resp_status(str(e)))

            # - если обучение прошло успешно
            # * берём последнюю версию из data/learn_data.version (если нет, => 0);
            ver = self._read_learn_data_ver()
            # * инкремент версии, и добавляем в корень структуры обучающих данных поле 'version'
            #   с новой версией.
            ver += 1
            ldata.data_tree['version'] = ver
            # * сохраняем обучающие данные
            with open(self._get_learn_data_file_name(ver), 'wb+') as fd:
                s = json.dumps(ldata.data_tree, ensure_ascii=False, indent=2)
                fd.write( s.encode('utf8') )

            # * сохраняем в файл data/learn_data.version новую версию.
            self._write_learn_data_ver(ver)
            Log("Learn SUCCESS")

            # разлочиваемся
            lock_fd.close()

            return (content_type, self._resp_status("OK"))

    def _resp_status(self, err):
        return '{ "status": "%s" }' % err

    #-------------------------------------------------------
    def _read_learn_data_ver(self):
        ver = 0
        try:
            with open( self.cfg['learn_data.version'] ) as fd:
                ver = int( fd.read() )
        except:
            pass
        return ver

    def _write_learn_data_ver(self, ver):
        try:
            with open( self.cfg['learn_data.version'], 'wb+' ) as fd:
                fd.write( str(ver) )
        except:
            return False
        return True

    def _get_learn_data_file_name(self, ver=None):
        if ver == None:
            ver = str(self._read_learn_data_ver())
        return self.cfg['learn_data.file'] + '.' + str(ver)

    def _read_learn_data(self, ver=None):
        try:
            with open( self._get_learn_data_file_name(ver) ) as fd:
                return fd.read()
        except Exception, e:
            Log("Can't read learn data: %s" % str(e))
            return None
