# -*- coding: utf-8 -*-

#
# Config
#

import json
import datetime

import logger

#-----------------------------------------------------------------------------------------------------------------------
class Config:
    #---------------------------------------------------------------------------
    def __init__(self, fname = ''):
        self.filename = None
        self.p = None
        if len(fname) > 0:
            self.load(fname)

    #---------------------------------------------------------------------------
    # get() via [] operator
    def __getitem__(self, param_path):
        return self.get(param_path)

    #---------------------------------------------------------------------------
    # Parts of param-path are separated by dot '.'
    # Example: cfg.get('common.local_dir')
    # Returns the 'default' value if param not found.
    def get(self, param_path, default = None):
        param_seq = []
        try:
            param_seq = param_path.split('.')
        except Exception, e:
            raise Exception("Config: Can't split param '%s', exception: '%s'" % (param_path, str(e)))
        p = self.p
        for pname in param_seq:
            p = p.get(pname, None)
            if p == None:
                if default == None:
                    raise Exception('Config: parameter "%s" did not found in config' % str(param_seq))
                p = default
                break
        return p

    #---------------------------------------------------------------------------
    # Parts of param-path are separated by dot '.'
    # Example: cfg.set('common.local_dir', '/mnt/disk1/sugg2.data')
    def set(self, param_path, value):
        param_seq = []
        try:
            param_seq = param_path.split('.')
        except Exception, e:
            raise Exception("Config: Can't split param '%s', exception: '%s'" % (param_path, str(e)))
        # check the path existance
        p = self.p
        for pname in param_seq:
            p = p.get(pname, None)
            if p == None:
                raise Exception('Config: parameter "%s" did not found in config' % str(param_path))
        # set the value
        self.add(param_path, value)

    #---------------------------------------------------------------------------
    def add(self, param_path, value):
        param_seq = []
        try:
            param_seq = param_path.split('.')
        except Exception, e:
            raise Exception("Config: Can't split param '%s', exception: '%s'" % (param_path, str(e)))
        # lay the path even it doesn't exist
        p = self.p
        i = 0
        while i < len(param_seq)-1:
            pname = param_seq[i]
            i += 1
            p[pname] = p.get(pname, {})
            p = p[pname]
        # let
        pname = param_seq[len(param_seq)-1]
        p[pname] = value

    #---------------------------------------------------------------------------
    def load(self, fname):
        self.filename = fname
        try:
            fp = open(fname)
            self.p = json.load(fp, encoding='utf-8')
        except Exception, e:
            logger.Log("ERROR while reading config-file: '%s'" % str(e))
            self.filename = None
            self.p = None
            return False
        return True

    #---------------------------------------------------------------------------
    def is_loaded(self):
        return (self.p != None)

    #---------------------------------------------------------------------------
    def save(self, fname = ''):
        if len(fname) == 0:
            fname = self.filename
        if fname == None:
            raise Exception("Specify filename to save config")
        try:
            fp = open(fname, 'wb+')
            json.dump(self.p, fp, ensure_ascii=False, indent=4, encoding='utf-8', sort_keys=True)
        except Exception, e:
            logger.Log("ERROR while writing config-file: '%s'" % str(e))
            return False
        return True
