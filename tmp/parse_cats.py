#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Парсит тектсовое представление категорий и суб-категорий в json.
# (!) Не более 2х уровней!
#

import os
import sys
import json

h = list()
i = 0
p = ''

for line in sys.stdin:
    line = line.rstrip().decode('utf-8')
    if line[0] != ' ':
        p = line
        i = len(h)
        cat = { 'name':p, 'subcats': [] }
        h.append( cat )
    else:
        line = line.strip()
        sub = h[i]
        sub['subcats'].append( {'name':line} )

sss = json.dumps( h, ensure_ascii=False, indent=2, sort_keys=True )
print sss.encode('utf-8')

