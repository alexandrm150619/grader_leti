"""
Импортирует код решения, полученный от студента и тест решения, 
написанный преподавателем как модули. Тесты решений должны находиться
в папке 'problems' и носить название {PROBLEM-ID}, которое соответсвует
<grader_payload> {"problem_name": "PROBLEM-ID"} </grader_payload> 
определенной прооблемой, определнной в курсе Open Edx.

Такой тестовый файл должен содержать одну из двух функций:

Если задание требует написаь функцию или сохранить результат в переменную
для его решения
def check(code):
    ...
    return result

Если задание требует использовать функцию пользовательского ввода input()
для ввода исходных данных и функцию вывода print() для вывода решения
def check_inout(code):
    ...
    return result

Данные функции используют загруженный модуль с пользовательским кодом решения
и возвращаают список словарей, представляющих все тестовые случаи.
Словари должны быть в одном из следующих форматов:
{'correct': (bool), 'function': (str), 'result': (str), 'expected': (str)}
{'correct': False, 'error': (str)}

"""
import importlib
import sys
import json
import re
import traceback
from io import StringIO


class StdToString:
    """Перенаправляет stdout и stderr в строковые переменные."""
    def __enter__(self):
        """Перенаправляет stdout и stderr в строковые переменные.
        Возвращает:
            new_stdout (StringIO): Перенаправленный stdout
            new_stderr (StringIO): Перенаправленный stderr
        """
        new_stdout = StringIO()
        new_stderr = StringIO()
        sys.stdout = new_stdout
        sys.stderr = new_stderr
        return (new_stdout, new_stderr)
    def __exit__(self, *args):
        """Устанавливает stdout и stderr обратно к стандартным значениям."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


def main():
    with StdToString():
        # Загрузка решения
        problem = str(sys.argv[1])
        try:
            solution = importlib.import_module('problems.{}'.format(problem))
        except ModuleNotFoundError:
            result = {'correct': False, 'error': 'Решение для проблемы {} отсутсвует'
                                                 .format(problem)}
            return result

        # Этот try используется для вылавливания исключений в пользовательском коде
        # при его импорте или при его запуске при помощи grading_function(code)
        try:
            # Импортируем пльзовтаельский код
            # Либо как модуль либо как строку (string)
            # Строка (string) используется для перенаправления input() 
            # в пользовательскуом коде перед его оценкой
            usercode = str(sys.argv[2]).split('.')[0]
            if hasattr(solution, 'check_inout'):
                grading_function = solution.check_inout
                with open(('tmp/{}.py'.format(usercode)), 'r') as f:
                    code = f.read()

            elif hasattr(solution, 'check'):
                grading_function = solution.check
                try:
                    code = importlib.import_module('tmp.{}'.format(usercode))
                # Обрабатывает ошибки в пользовательском коде при его импорте
                except ModuleNotFoundError:
                    result = {'correct': False,
                              'error': 'Ошибка при загрузке пользовательского кода. '
                                       'Попробуйте снова.'}
                    return result

            else:
                # Происходит в случае некоррктного написания файла правильного решения
                result = {'correct': False,
                          'error': 'Решение для проблемы {} работает некорректно. '
                                   .format(problem)}
                return result

            # Вызываем функцию оценки (check или check_inout)
            result = grading_function(code)

        except EOFError:
            # Возникает если пользовательский код содержит больше input(), чем требует задание
            result = {'correct': False,
                      'error': 'EOFError: Добавлено больше `input()` чем требовалось'}

        except SyntaxError as err:
            # Возникает при синтаксических ошибках в пользовательском коде
            message = traceback.format_exc(limit=0)
            message = re.sub('(?<=File ")[^"]*', 'Usercode', message)
            result = {'correct': False, 'error': message}

        except BaseException:
            # Оставшиеся неперехваченные исключения
            result = {'correct': False, 'error': traceback.format_exc(limit=0)}
        return result


if __name__ == '__main__':
    # Возвращает результат. Так как используется print() grader.py может считать
    # его из stdout. Во время исполнения stdout и stderr были перенаправлены, поэтому
    # это единственное, что будет в них напечатано
    print(json.dumps(main()))
