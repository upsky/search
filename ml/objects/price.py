#!/usr/bin/env python
# -*- unicode: utf-8 -*-

import os
import sys

'''
PAbout Price Curr
PAbout Price Mult
PAbout PriceFrom "-" PriceTo Mult
PEq Price Curr
PEq Price Mult
PEq Price Mult Curr
PEq PriceFrom PriceTo Mult
PEq PriceFrom "-" PriceTo Mult
PFrom PriceFrom "-" PTo PriceTo Mult Curr
PFrom PriceFrom Curr
PFrom PriceFrom PTo PriceTo Curr
PFrom PriceFrom PTo PriceTo Mult
PTo PriceTo Curr
PTo PriceTo Mult
PTo PriceTo Mult Curr
PTo PriceWritten Curr
PTo PriceWritten Mult
'''

kPrepEq 	= 1
kPrepFrom 	= 2
kPrepTo 	= 3
kPrepAbout	= 4

kPrep = {
	kPrepEq: 	['за', 'по', 'цена'],
	kPrepFrom: 	['от'],
	kPrepTo: 	['до', 'не дороже'],
	kPrepAbout: ['около', 'в пределах', 'в диапазоне', 'диапазон']
}

#-----------------------------------------------------------
class Price:
	def __init__(self, ):
		self.prep = []
		self.value = []
		self.mult = []
		self.curr = []

	def parse(str):
		#



'''
	Price = [0-9]+([.,]?[0-9]{3})* <-- пробел внутри цены не делаем, т.к. если в гугле спросить голосом "машина за 500 600 тысяч", то между цифрами так и будет пробел. Нужно брать токены последовательно, а уже потом по предлогам и мультипликаторам ориентироваться что есть что.
	PriceFrom = Price
	PriceTo = Price
	PriceWritten = ... целый разбор
	Mult = 'тыс', 'тысяч', 'тысячи', 'млн', 'миллион', 'миллиона', 'миллионов'
	Curr = 'рубли', 'рублей', 'рубля', 'руб', 'р', '$', 'уе', 'у.e.'
	Delim = [\s\-]
'''

