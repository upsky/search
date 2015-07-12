#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Парсит тектсовое представление категорий и суб-категорий в json.
# (!) Не более 2х уровней!
#

import os
import sys
import json

kDefaultTuple = tuple( ({'id':0}, {}) )

h = {}
c = ''
c_sub = ''
i = 0

for line in sys.stdin:
    line = line.rstrip().decode('utf-8')
    if len(line) == 0:
        continue

    i += 1

    if line[0] != ' ':
        c = unicode(line)
        h[c] = ({'id':i}, {})
    else:
        line = line.strip()
        c_sub = line
        sub = h[c][1]
        sub[c_sub] = ({'id':i}, {})

sss = json.dumps( h, ensure_ascii=False, indent=2, sort_keys=True )
print sss.encode('utf-8')

