# -*- coding: utf-8 -*-

import datetime
import sys

#-------------------------------------------------------------------------------
kGlobalIdent = 0

#-------------------------------------------------------------------------------
def Log(msg, ident = 0):
    if ident == 0 :
        ident = kGlobalIdent
    now = datetime.datetime.now()
    ident_str = ' ' * ident
    fmt = "[%0.4u-%0.2u-%0.2u_%0.2u:%0.2u:%0.2u]%s %s" % (now.year, now.month, now.day, now.hour, now.minute, now.second, ident_str, msg)
    print >> sys.stderr, fmt

#-------------------------------------------------------------------------------
# Удобный инструмент для вложенных шагов: лог-отчёты дочерних шагов будут печататься "глубже".
# + Этот класс - автоматическая подстраховка выравнивания логгера от случайных exception'ов - класс автоматически
# обеспечит возврат к исходному выравниванию.
class ScopeIdentHolder:
    def __init__(self, push_ident):
        global kGlobalIdent
        self.old_ident = kGlobalIdent
        self.push_ident = push_ident

    def push(self):
        global kGlobalIdent
        kGlobalIdent += self.push_ident

    def pop(self):
        global kGlobalIdent
        kGlobalIdent -= self.push_ident

    def __del__(self):
        global kGlobalIdent
        kGlobalIdent = self.old_ident

