# -*- coding: utf-8 -*-

import re

#-------------------------------------------------------------------------------
class Matcher:
    def __init__(self):
        self.r = {}
        self.begin_re = re.compile(r'(?P<word>[\w]+)|(?P<sp>\s+)|(?P<label><[\w_0-9]+>)|(?P<re_begin>[(])', flags=re.UNICODE)
        self.err_msg = ''

    #-------------------------------------------------------
    def add_rules(self, name, rules):
        self.err_msg = ''

        for (label, rule_arr) in rules.iteritems():
            if rule_arr is str:
                rule_arr = [rule_arr]

            for r in rule_arr:
                rule_name = name + '__' + label
                res = self.parse_rule(r)
                if res == None:
                    return False
                self.r[rule_name] = res

        return True

    #-------------------------------------------------------
    def parse_rule(self, rule):
        if len(rule) == 0:
            err_msg = "rule is empty"
            return None

        try:
            rule = rule.decode('utf-8')
        except Exception, e:
            err_msg = "can't decode rule from utf-8 to unicode, exc: " + str(e)
            return None

        i = 0
        ready = ''
        while i < len(rule):
            z = self.begin_re.match(rule[i:])
            if z == None:
                err_msg = "unknown rule-token at position %d" % i
                return None
            if z.group('word'):
                i += ...
                stemming of word ...
                ready += stemmed_word
            elif z.group('sp'):
                i += ...
                ready += '[\s]+'
            elif z.group('label'):
                i += ...
                label = ...
                y = self.r.get(label, None)
                if y == None:
                    err_msg = "unknown rule with label <%s>" % label
                    return None
                ready += y
            elif z.group('re_begin'):
                ... stacked parsing of '('s ...

