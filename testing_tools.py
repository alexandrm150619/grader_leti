""" 
Вспомогательные функции для тестирования пользовательских решений.

Вспомогательная функция должна возвращать словарь или список из словарей, каждый
из которых представляет одного тестового случая в одном из следующих форматов:
{'correct': (bool), 'function': (str), 'result': (str), 'expected': (str)}
{'correct': False, 'error': (str)}
"""
import sys
import traceback

from util import print_log


def test_function(function=None, values=None, solution=None, expected=None):
    """
    Сравнивает пользовательскую функцию с функцией, написанной преподователем
    или с заданным списком ожидаемых результатов вывода

    Аргументы:
        function (function): тестируемая функция
        values (list): список тестовых значений. Выглядит как [(0,1), (2,4), ...] 
                       или [3, 4, 6, 9, ...]. В первом случае вызываем `function(*val)`
                       для каждого элемента в списке, во втором - `function(val)` для
                       каждого `val` в таком списке.
        solution (function): функция, которая возвращает правильные результаты при
                             вызове `solution(val)`
        expected (list): список ожидаемых результатов работы функции.
        show_expected (bool): флаг скрытия корректного ответа при выводе в See Full Output

    Замечание:
        Вы должны определить при вызове либо только `solution` либо только `expected`.

    Возвращает:
        result (list): Список из результатов тестирования.
    """

    if solution is None and expected is None:
        print_log("При вызове `testing_tools.test_function` нужно определить 'solution' или 'expected'!")
        raise ValueError("Ожидался один из следующих аргументов: 'solution' или 'expected'.")
    elif solution is not None and expected is not None:
        print_log('При вызове `testing_tools.test_function` нужно определить'
                  "только либо 'solution' или только либо 'expected'!"
                  "'expected' будет проигнорирован.")

    result = []
    for i, val in enumerate(values):
        try:
            iter(val)
        except TypeError:
            val = list(val)
        else:
            if isinstance(val, str):
                val = [val]

        out = dict()

        # Создаем текстовую информацию для тестируемого случая
        out['function'] = '{}({})'.format(function.__name__, ', '.join(
            "'{}'".format(v) if isinstance(v, str) else str(v) for v in val))

        # Получаем корректное ожидаемое решение
        if solution is not None:
            out['expected'] = solution(*val)
        else:
            out['expected'] = expected[i]

        # Получаем пользовательское решение
        try:
            out['result'] = function(*val)
        except Exception as err:
            out['result'] = '{}: {}'.format(type(err).__name__, str(err))
            out['correct'] = False
        else:
            out['correct'] = bool(out['result'] == out['expected'])

        result.append(out)
    return result


def test_input_print(code, values, solution=None, expected=None):
    """
    Тестирует пользовательский код с использованием `input` и `print`

    Используется для пользовательского кода с одиночным вводом исходного 
    значения через `input` и с возвращением результата через `print`.

    Аргументы:
        code (str): пользовательский код в виде строки.
        values (list): список тестовых значений в формате [val1, val2, val3, ...]
                       При вызове `input()` он возвращает `str(val1)`.
        solution (function): функция, которая возвращает правильные результаты при
                             вызове `solution(val)`
        expected (list): список ожидаемых результатов работы функции.
        show_expected (bool): флаг скрытия корректного ответа при выводе в See Full Output

    Замечание:
        Вы должны определить при вызове либо только `solution` либо только `expected`.

    Возвращает:
        result (list): Список из результатов тестирования.
    """
    if solution is None and expected is None:
        print_log("При вызове `testing_tools.test_input_print` нужно определить 'solution' или 'expected'!")
        raise ValueError("Ожидался один из следующих аргументов: 'solution' или 'expected'.")
    elif solution is not None and expected is not None:
        print_log('При вызове `testing_tools.test_input_print` нужно определить'
                  "только либо 'solution' или только либо 'expected'!"
                  "'expected' будет проигнорирован.")

    # Перезапись встроенной функции input()
    class Input(): 
        """Перезаписывает встроенную функцию input()."""
        def __init__(self, value):
            self.value = str(value)

        def __call__(self, msg=''):
            # вызов `input()` в пользовательском коде вернет `str(value)`.
            return self.value

    result = []
    for i, val in enumerate(values):
        input = Input(val)

        # Создаем текстовую информацию для тестируемого случая
        out = dict()
        out['function'] = 'Testing with input: {}'.format(val)

        # Получаем корректное ожидаемое решение
        if solution is not None:
            out['expected'] = solution(val)
        else:
            out['expected'] = expected[i]

        # Получаем пользовательское решение
        try:
            sys.stdout.truncate(0)
            exec(code, locals())
            # sys.stdout будет перенаправлен в StringIO
            out['result'] = sys.stdout.getvalue().strip('\u0000\n')
        except Exception:
            out['error'] = traceback.format_exc(limit=0)
            out['correct'] = False
        else:
            out['correct'] = bool(out['result'] == out['expected'])

        result.append(out)
    return result

def test_variable(answer, expected):
    """
    Тестирует пользовательский код, в котором вычисленный пользователем ответ сохранен в переменной

    Аргументы:
        answer (list): список пользовательских результатов вычислений.
        expected (list): список ожидаемых результатов работы функции.
        show_expected (bool): флаг скрытия корректного ответа при выводе в See Full Output

    Замечание:
        При вызове нобходимо определить `expected`.

    Возвращает:
        result (list): Список из результатов тестирования.
    """

    if expected is None:
        print_log("При вызове `testing_tools.test_variable` нужно определить 'expected'!")
        raise ValueError("Ожидался аргумент 'expected'.")

    result = []
    for i, val in enumerate(expected):
        out = dict()

        # Создаем текстовую информацию для тестируемого случая
        out['function'] = 'This value shoud equals to {}'.format(val)

        # Получаем корректное ожидаемое решение
        out['expected'] = expected[i]

        # Получаем пользовательское решение
        try:
            out['result'] = answer[i]
        except Exception:
            out['error'] = traceback.format_exc(limit=0)
            out['correct'] = False
        else:
            out['correct'] = bool(out['result'] == out['expected'])

        result.append(out)
    return result