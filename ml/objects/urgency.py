# -*- coding: utf-8 -*-

import re

from lex import gLexer

from objects import kAnalyzersSection

#-------------------------------------------------------------------------------
kVocab = ['помогите', 'срочно', 'срочняк', 'немедленно', 'в ближайшее время',
          'поспешно', 'безотлагательно', 'спешно',
          'неотложно', 'безотложно', 'экстренно', 'неотлагательно', 'незамедлительно',
          'немедля', 'сейчас же', 'щас же', 'не откладывая', 'без промедления', 'чрезвычайно',
          'без задержки', 'в срочном порядке', 'в спешном порядке', 'в пожарном порядке',
          'без малейшего отлагательства', 'быстро', 'бегом',
          'ну ка', 'ну-ка', 'я сказал' ]
'''
          'сейчас',
          'скорая помощь', 'пожар', 'инфаркт', 'инсульт', 'человеку плохо',
          'дыхание', 'зрачки', 'пульс', 'потерял сознание', 'обморок', 'течет кровь', 'кровотечение'
'''

#-------------------------------------------------------------------------------
class Analyzer:
    def __init__(self, config, voc=kVocab):
        self.name = 'objects.urgency'
        self.err_msg = None

        self.cfg = config

        # нормализуем словарь
        voc_list = []
        for s in voc:
            s = s.decode('utf-8')
            s = gLexer.normalize_str( s )
            voc_list.append( s )

        # генерим регулярку
        voc_rx = u'|'.join(voc_list)
        self.voc_re = re.compile(voc_rx, flags=re.UNICODE)

    #-------------------------------------------------------
    def get_name(self):
        return self.name

    #-------------------------------------------------------
    def get_err_msg(self):
        return self.err_msg

    #-------------------------------------------------------
    def analyze(self, query):
        obj = self.voc_re.search( query.text_normalized )
        if obj == None:     # просто ничего не нашли
            return True

        query.add_label(kAnalyzersSection, self.name, {'start':obj.start(0), 'end':obj.end(0)} )
        return True

