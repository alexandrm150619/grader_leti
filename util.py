"""
В данном модуле содержатся вспомогатльные функции, используемые в остальных модулях.
"""

import time
import datetime
import random

def print_log(str):
    """
    Функция для печати логов с указанием времени в терминал, где запущен грейдер.

    Аргументы:
            str (string): сообщение, которое необходимо вывести в терминал.
    """
    now = datetime.datetime.now()
    print('{} {}.'.format(now.strftime("%d-%m-%Y %H:%M"), str))

def generate_random_filename():
    """
    Функция для генерации случайного имени для файла
    """
    return '_'.join([time.strftime('%Y%m%d%H%M%S'),
                     str(time.time()).split('.')[-1],
                     str(random.random()).split('.')[-1]])