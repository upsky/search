#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

import norm
import ngrams

#
# Класс загружает сущности из файла сущностей.
# Нормализует фразы сущностей по регистру, букве ё и морофологически.
#

#-------------------------------------------------------------------------------
# fname - имя файла с сущностями и их фразами
# basepath - базовый путь для словарей, которые указаны в файле сущностей
class Entities( object ):
    def __init__(self, fname=None, basepath=''):
        super(Entities, self).__init__()
        if fname is None:
            self._init()
        else:
            self.load(fname, basepath)

    def _init(self, fname=None, basepath=''):
        self.phrase2idweight = {}     # phrase -> list(id, weight)
        self.entity_id = 0
        self.ent_id2name = {}   # id -> name of entity
        self.ent_name2id = {}   # name -> id of entity
        self.fname = fname
        self.basepath = basepath

    #---------------------------------------------
    def load(self, fname, basepath, normalize=True):
        self._init(fname, basepath)

        entity_name = ''
        entity_weight = 1.0;
        entity_phrases = []

        nnn = 0
        for line in open(fname):
            nnn += 1

            line = line.rstrip('\r\n').decode('utf-8')
            line_stripped = line.strip()

            if len(line) == 0 or len(line_stripped) == 0:
                continue
            # comment
            if line_stripped[0] == '#':
                continue

            # отступ хотя бы из 2х пробелов или табуляции - словосочетание текущей сущности
            if (len(line) > 2 and line[0] == u' ' and line[1] == u' ') or line[0] == u'\t':
                if len(entity_name) == 0:
                    raise Exception("%s:%d: No entity name for phrase '%s'" % (fname, nnn, line_stripped))
                # парсим строку с фразой + возможные параметры
                (phrase, params) = self._parse_line(line_stripped, fname, nnn)
                if normalize:
                    phrase = norm.norm_phrase(phrase, morph=True)
                weight = params.get('w', entity_weight)
                entity_phrases.append( (phrase, weight) )
                continue

            # нет отступа - название сущности, сохраняем предыдущую сущность
            if len(entity_phrases) > 0:
                self._add_entity(entity_name, entity_phrases, fname, nnn)

            entity_name = u''
            entity_weight = 1.0;    # дефолтный вес для всех фраз данной сущности
            entity_phrases = []     # list( (phrase, weight) ) - фраза и её вес для данной сущности

            # теперь создаём новую сущность
            (entity_name, params) = self._parse_line(line_stripped, fname, nnn)

            entity_weight = params.get('w', entity_weight)
            phrases = params.get('file', None)
            if not phrases is None:
                for ph in phrases:
                    if normalize:
                        ph = norm.norm_phrase(ph, morph=True)
                    entity_phrases.append( (ph, entity_weight) )

        # сохраняем последнюю сущность
        if len(entity_phrases) > 0:
            self._add_entity(entity_name, entity_phrases, fname, nnn)

    #---------------------------------------------
    # По фразе найти список сущностей и весов. Каждая фраза может относиться к нескольким сущностям, с разными весами.
    # [ (entity_id, weight, count) ] -- id сущности, вес фразы для данной сущености, кол-во найденных сущностей
    # nglen - макс. длина искомой фразы; TODO: сделать автоматическое определение по исходному словарю сущностей-фраз
    def get_entities(self, phrase, nglen=3, normalize=True):
        if normalize:
            phrase = norm.norm_phrase(phrase, morph=True)
        ngs = {}
        ngrams.split2ngrams(phrase, nglen, ngs)
        res = []
        for (ng_str, ng_cnt) in ngs.iteritems():
            idw_list = self.phrase2idweight.get(ng_str, None)
            if idw_list is None:
                continue
            for (id, weight) in idw_list:
                res.append( (id, weight, ng_cnt) )

        return res

    #---------------------------------------------
    def _add_entity(self, entity_name, entity_phrases, gdb_fname, gdb_nnn):
        if entity_name in self.ent_name2id:
            raise Exception("%s:%d: duplicate entity name '%s'" % (dbg_fname, dbg_nnn, entity_name))
        # уникализуем фразы
        uniq_phrases = {}
        for (phrase, weight) in entity_phrases:
            uniq_phrases[phrase] = weight
        entity_phrases = [(ph, w) for (ph, w) in uniq_phrases.iteritems()]
        # добавляем
        self.entity_id += 1
        self.ent_id2name[self.entity_id] = entity_name
        self.ent_name2id[entity_name] = self.entity_id
        for (phrase, weight) in entity_phrases:
            self.phrase2idweight[phrase] = self.phrase2idweight.get(phrase, [])
            # одна фраза может относится к разным сущностям, с разным весом
            self.phrase2idweight[phrase].append( (self.entity_id, weight) )

    #---------------------------------------------
    # Распарсить строчку файла сущностей; у каждой сущности или фразы могут быть параметры.
    # result: ( thing_str, {param_name:value} )
    def _parse_line(self, line, dbg_fname, dbg_nnn):
        fld = line.strip().split(',')

        thing_name = fld[0].strip()
        if len(thing_name) == 0:
            raise Exception("%s:%d: Empty thing at this line" % (dbg_fname, dbg_nnn))

        # сущность с параметрами?
        params = {}
        for i in xrange(1, len(fld)):
            prm = fld[i].split(u'=')
            if prm[0].strip() == u'file':
                if len(prm) < 2:
                    raise Exception("%s:%d: Bad file param; proper format: your_thing, file=/path/to/file" % (dbg_fname, dbg_nnn))
                dict_fname = os.path.join(self.basepath, prm[1].strip(' "\''))
                try:
                    print >> sys.stderr, "Entities: loading external dictionary '%s'" % dict_fname
                    phrases = open(dict_fname).readlines()
                except Exception, e:
                    raise Exception("%s:%d: Can't read file '%s' for thing '%s', exc: %s" % (dbg_fname, dbg_nnn, dict_fname, thing_name, str(e)))
                new_phrases = []
                for ph in phrases:
                    ph = ph.strip().decode('utf-8')
                    if len(ph) == 0 or ph[0] == '#':    # пропускаем пустые и закомменченные строки
                        continue
                    new_phrases.append( ph )
                params['file'] = new_phrases
            elif prm[0].strip() == u'w':
                if len(prm) < 2:
                    raise Exception("%s:%d: Bad weight param; proper format: your_thing, w=1.0" % (dbg_fname, dbg_nnn))
                try:
                    w = float(prm[1])
                except Exception, e:
                    raise Exception("%s:%d: Bad weight value '%s'; must be float" % (dbg_fname, dbg_nnn, prm[1].encode('utf-8')))
                params['w'] = w
            else:
                raise Exception("%s:%d: Unknown parameter '%s'" % (dbg_fname, dbg_nnn, prm[0].encode('utf-8')))

        return (thing_name, params)

    #---------------------------------------------
    def _print_all(self):
        for (phrase, iwd_list) in self.phrase2idweight.iteritems():
            for (id, weight) in iwd_list:
                name = self.ent_id2name[id]
                s = u'\t'.join( [phrase, name, unicode(id), unicode(weight)] )
                print s
