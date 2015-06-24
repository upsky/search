#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ...lex import tokenizer
from ...lex import normalizer


kVocab = [u'помогите', u'срочно', u'срочняк', u'немедленно', u'поспешно', u'безотлагательно', u'сейчас', u'спешно',
          u'неотложно', u'безотложно', u'экстренно', u'неотлагательно', u'незамедлительно',
          u'немедля', u'сейчас же', u'щас же', u'не откладывая', u'без промедления', u'чрезвычайно',
          u'без задержки', u'в срочном порядке', u'в спешном порядке', u'в пожарном порядке',
          u'без малейшего отлагательства', u'быстро', u'бегом',
          u'ну ка', u'ну-ка', u'я сказал',
          ''' u'скорая помощь', u'пожар', u'инфаркт', u'инсульт', u'человеку плохо',
          u'дыхание', u'зрачки', u'пульс', u'потерял сознание', u'обморок', u'течет кровь', u'кровотечение' ''']

#-----------------------------------------------------------
class Detector:
    def __init__(self,
                 voc=kVocab,
                 tokenizer=tokenizer.WordsTokenizer(),
                 normalizer=normalizer.StemmedNormalizer()):
        self.tokenizer = tokenizer
        self.normalizer = normalizer

        # нормлизуем словарь
        self.voc = []
        for s in voc:
            wlist = []
            for w in self.tokenizer.tokenize(s, tokenize=self.tokenizer.tokenize):
                wlist.append( w )
            s = ' '.join(wlist)
            self.voc.append( s )

    def search(ustr):
        wlist = []
        for w in self.tokenizer.tokenize(ustr, tokenize=self.tokenizer.tokenize):
            wlist.append( w )
        ustr = ' '.join(wlist)

        # TODO: use Aho-Corasik for speed-up
        for sub_str in self.voc:
            if ustr.find(sub_str) != -1:
                return True

        return False

#-----------------------------------------------------------
if __name__ == "__main__":
    t = [(u'Срочно привезти рояль в центр москвы', True),
         (u'очень срочно привезти рояль', True),
         (u'нужно В срочном ПоРядке привезти мороженное пингвинам', True),
         (u'на улицу набитых фонарей требуется экстренная помощь', True),
         (u'требуется экстренная помощь на дороге! разорвало колесо!', True),
         (u'быстро на улицу дубаковская тёплого сантехника!', True),
         (u'в экстренном порядке нужно прибить табуретку к потолку!', True),
         (u'да нихрена мне не надо', False)]

    det = Detector()

    for (text, res) in t:
        if res != det.search(text):
            print "Wrong: " + text
