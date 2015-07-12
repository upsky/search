# -*- coding: utf-8 -*-

kAnalyzersSection = 'obj'

'''
Возможности языка разметки/синонимизации запроса:
    1. %произвольный порядок слов == %порядок произвольный слов == %слов порядок произвольный == %порядок слов произвольный
    2. необязательность? слов?
    3. #точное #совпадения #слова (без нормализации)
    4. любые * слова * между * указанными
    5. ^в началае запроса
    6. в конце запроса$
    7. (регулярное выражение в количестве [0-9]+ штук)
    8. <part_name> - в это место подставляется именованная часть, которая описана где-то выше
    9. \л\ю\б\о\й\ \с\имвол можно экранироват\ь, даже вот этот - \\; поэтому не бойтесь экранировать

example:
---------
# все токены запроса, по которым рас
my_group = {
    # пробелы между словами означают от 1го и более пробельных символов == [\s\t]+
    'label1': ['this thing', 'is the same', 'as', 'label1'],

    # если элемент 1, то массив не обязателен
    'label2': '(this thing|is the same|as|label1)', # except absent of morphology

    # Всё, что в (скобках) - регулярное вырежение; 1 пробел внутри регулярок означает ровно 1 пробел, 2 - 2, и т.д.
    # Для слов внутри регулярок нормализация не применяется. Поэтому можно взять слова в скобки чтобы
    # искать их ровно в той форме, которую нужно.
    # В <угловых> - подстановка где-то выше описанного элемента.
    'label3': ['word (regexp[0-9]* (alt1|alt2)+) <label1> <label2>'],
}
'''

obj_price = {
    # пробел внутри цены не делаем, т.к. если в гугле спросить голосом
    # "машина за 500 600 тысяч", то между цифрами так и будет пробел.
    # Нужно брать токены последовательно, а уже потом по предлогам и мультипликаторам
    # ориентироваться что есть что.
    'PriceVal': '([0-9]+([.,]?[0-9]{3})*)',
    'PriceFrom':'<PriceVal>',
    'PriceTo':  '<PriceVal>',
    'PEq':      ['за', 'по', 'цена'],
    'PFrom':    ['от'],
    'PTo':      ['до', 'не дороже'],
    'PAbout':   ['около', 'в пределах', 'в диапазоне', 'диапазон'],
    'Mult':     ['тыс', 'тысяч', 'тысячи', 'млн', 'миллион', 'миллиона', 'миллионов'],
    'Curr':     ['рубли', 'рублей', 'рубля', 'руб', 'р', '$', 'уе', 'у.e.'],
    'delim':    '([\s\-])',

    'PriceObj': ['<PAbout> <PriceVal> <Curr>',
                 '<PAbout> <PriceVal> <Mult>',
                 '<PAbout> <PriceFrom> <delim> <PriceTo <Mult>',
                 '<PEq> <Price> <Curr>',
                 '<PEq> <Price> <Mult>',
                 '<PEq> <Price> <Mult> <Curr>',
                 '<PEq> <PriceFrom> <PriceTo> <Mult>',
                 '<PEq> <PriceFrom> <delim> <PriceTo <Mult>',
                 '<PFrom> <PriceFrom> <delim> <PTo> <PriceTo> <Mult> <Curr>',
                 '<PFrom> <PriceFrom> <Curr>',
                 '<PFrom> <PriceFrom> <PTo> <PriceTo> <Curr>',
                 '<PFrom> <PriceFrom> <PTo> <PriceTo> <Mult>',
                 '<PTo> <PriceTo> <Curr>',
                 '<PTo> <PriceTo> <Mult>',
                 '<PTo> <PriceTo> <Mult> <Curr>',
                 '<PTo> <PriceWritten> Curr>',
                 '<PTo> <PriceWritten> Mult>']
}
