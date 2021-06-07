"""
Данный модуль содержит основные функции для работы грейдера: 
запуск, оценка пользовательского решения, парсинг запроса от XQueue,
создание ответа для XQueue.
Так же в данном модуле описан класс обработчика для принятия запросов от XQueue.
"""

import gc
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from json.decoder import JSONDecodeError
from socketserver import ThreadingMixIn

from util import print_log, generate_random_filename

class Handler(BaseHTTPRequestHandler):
    """Обработчик для запросов XQueue."""
    def do_HEAD(self):
        pass

    def do_GET(self):
        pass

    def do_POST(self):
        # Метод для обработки POST запроса
        start = time.time()
        content_len  = int(self.headers['Content-Length'])
        post_body = self.rfile.read(content_len ).decode()

        try:
            body_content = json.loads(post_body)
        except JSONDecodeError:
            print('JSONDecodeError, post_body не было загружено должным образом.')
        else:
            problem_name, hide_answer, student_response, user_id = get_info(body_content)

            if hide_answer == "True":
                hide_answer = True
            else:
                hide_answer = False
            print(hide_answer)

            # Выполняем оценку пользоательского ответа на задание
            print_log('User with id {} submitted code for problem {}.'.format(user_id, problem_name))
            result = grade(problem_name, student_response, hide_answer)

            # Отправляем ответ XQueue, содержащий результаты проверки
            send = json.dumps(result).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(send)

            print_log('Submittedd code from user with id {} was graded in {} sec.'.format(user_id, time.time()-start))


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ 
        Этот класс позволяет обрабатывать запросы в различных потоках. 
    """


def grade(problem_name, student_response, hide_answer):
    """
    Функция оценки пользовательского решения

    Аргументы:
        problem_name (str): название оцениваемой проблемы
        student_response (str): строка, содержащая код, отправленный пользователем на проверку

    
    Возвращает:
        msg (byte): дамп JSON ответа для XQueue. Содержит словарь
                    {'correct': (bool), 'score': (float), 'msg': (str)}
                    где
                    correct (bool): общий результат
                    score (float): процент успеха прохождения тестов в виде от 0 до 1
                    msg (str): отформатированные в HTML код результаты тестов
    """
    try:
        random_filename = generate_random_filename()

        # Создаем временный каталог tmp, если он не существует
        if not os.path.exists('tmp'):
            print_log('Создание каталога ./tmp')
            os.makedirs('tmp')

        # Создание файла с кодом python для тестирования из отправленного пользователем решения
        student_program = 'Program{}_{}'.format(problem_name, random_filename)
        source_file = open('tmp/{}.py'.format(student_program), 'w')
    
        source_file.write(student_response)
        source_file.close()
        
        # Выполняем в новом процессе дочернюю программу
        process = subprocess.Popen(['python3',
                                    'tester.py',
                                    problem_name, student_program],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        timeout = 30
        try:
            # Запущенный процесс отработает 30 секунд,
            # если время истечет и реезультат работы не
            # будет получен, то будет выброшено исключение
            out, error = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            result = {'correct':False, 'error': 'Время оценки истекло за {} секунд. \n'
                                                'Проверьте код на бесконечный цикл.'.format(timeout)}
        else:
            if error:
                print_log('Тестировщик упал: {}', error.decode())
                result = {'correct':False, 'error':error.decode()}
            else:
                if isinstance(out, bytes):
                    out = out.decode('utf-8')
                try:
                    result = json.loads(out)

                except JSONDecodeError:
                    print_log('JSONDecodeError: {}'.format(traceback.format_exc()))
                    result = {'correct':False, 'error': 'Ошибка при оценке кода, проверьте синтаксис.'}

            # Удаляем пользовательскую программу после тестирования
            os.remove('tmp/{}.py'.format(student_program))

        gc.collect()

    except Exception:
        result = {'correct':False, 'error': 'Произошла системная ошибка'}          

    # Формируем ответ XQueue с результатами проверки
    result = create_response(result, hide_answer)

    return result

def create_response(result, hide_answer):
    """ 
    Получает список результатов тестов и создает ответ для XQueue.
    Результты тестирования форматируются HTML кодом.

    Аргументы:
        result (list): Список тестов, каждый тест представлен словарем.
                       Каждый тест должен соответсвовать одному из форматов:
                       {'correct': (bool), 'function': (str),
                        'result': (str), 'expected': (str)}
                       или
                       {'correct': False, 'error': (str)}
                       где применяются следующие обозначения:
                       correct (bool): результат теста
                       function (str): опиание теста
                       result (str): вывод программы обучающегося
                       expected (str): корректный и ожидаемый результат
                       error (str):  сообщение об ошибке, которая не дала
                                     провести тест(SyntaxError, NameError, и т.д.)

    Возвращает:
        msg (byte): дамп JSON ответа для XQueue. Содержит словарь
                    {'correct': (bool), 'score': (float), 'msg': (str)}
                    где
                    correct (bool): общий результат
                    score (float): процент успеха прохождения тестов в виде от 0 до 1
                    msg (str): отформатированные в HTML код результаты тестов
    """

    start = """
            <div class="test">
                <header>Test results</header>
                <section>
                    <div class="shortform">
                    {}
                    <a href="#" class="full full-top">See full test results</a>
                    </div>
            <div class="longform" style="display: none;">
            """

    end = """</div></section></div>"""

    correct =  """
                <div class="result-output result-correct">
                    <h4>{header}</h4>
                    <pre>{function}</pre>
                    <dl>
                        <dt>Output:</dt>
                        <dd class="result-actual-output"><pre>{result}</pre></dd>
                    </dl>
                </div>
                """
    
    correct_hidden =  """
                <div class="result-output result-correct">
                    <h4>{header}</h4>
                </div>
                """
    wrong = """
            <div class="result-output result-incorrect">
                    <h4>{header}</h4>
                    <pre>{function}</pre>
                    <dl>
                        <dt>Your output:</dt>
                        <dd class="result-actual-output"><pre>{result}</pre></dd>
                        <dt>Correct output:</dt>
                        <dd><pre>{expected}</pre></dd>
                    </dl>
            </div>
            """
    wrong_hidden = """
            <div class="result-output result-incorrect">
                    <h4>{header}</h4>
            </div>
            """

    fatal = """
            <div class="result-output result-incorrect">
                <h4>Error</h4>
                <dl>
                <dt>Message:</dt>
                <dd class="result-actual-output"><pre>{error}</pre></dd>
                </dl>
            </div>
            """

    out = {}

    # Объединяем одиночный результат теста в список
    if isinstance(result, dict):
        result = [result]
    
    if not result:
        print_log('Пустой результат')
        result = [{'correct':False, 'error': 'Похоже, что произошла ошибка при проверке вашего кода.\n\n'
                                             'Пожалуйста, проверьте запускается ли он на вашем компьютере'}]

    # correct == True, если пройдены все тесты
    number_passed = sum(r['correct'] for r in result)
    out['correct'] = (number_passed == len(result))

    # Процент успеха прохождения тестов
    out['score'] = number_passed / len(result)

    # Результаты тестов в HTML формате
    # start содержит заголовок с общим сообщением и кнопками открытия подробных результатов
    if any(('error' in res) for res in result):
        html_message = start.format('ERROR')
    elif out['correct']:
        html_message = start.format('CORRECT')
    else:
        html_message = start.format('INCORRECT')

    # Средняя часть сообщения
    for i, res in enumerate(result):
        # Здесь объявляются состояния по умолчанию для всех составляющих
        answer = {'correct': False, 'function': '', 'result': '', 'expected': ''}
        answer.update(res)

        if 'error' in res:
            html_message += fatal.format(**answer)
        else:
            name = 'Test Case {}'.format(i+1)
            if hide_answer:
                if res['correct']:
                    html_message += correct_hidden.format(header=name)
                else:
                    html_message += wrong_hidden.format(header=name)
            else:
                if res['correct']:
                    html_message += correct.format(header=name, **answer)
                else:
                    html_message += wrong.format(header=name, **answer)

    # end закрывает все открытые HTML тэги
    html_message += end
    out['msg'] = html_message

    return out


def get_info(json_object):
    """
    Функция для парснга запроса к XQueue.

    Аргументы:
        json_object (): 

    Возвращает:
        problem_name (str): уникальный идентификатор задания
        student_response (str): код, полученный от обучающегося
        student_id
    """
    json_object = json.loads(json_object['xqueue_body'])
    grader_payload = json.loads(json_object['grader_payload'])
    student_response = json_object['student_response']
    student_id = json.loads(json_object['student_info']).get('anonymous_student_id', 'unknown')
    problem_name = grader_payload['problem_name']
    hide_answer = grader_payload['hide_answer']
    return problem_name, hide_answer, student_response, student_id

def start(host='localhost', port=1710):
    # Установка рабочей директории
    os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))

    # Запуск грейдера
    try:
        server = ThreadedHTTPServer((host, port), Handler)
        print('Grader started on {}:{}.'.format(host, port))
        print('Press Ctrl+C to stop grader')
        server.serve_forever()

    except KeyboardInterrupt:
        # Завершение работы грейдера при нажатии Ctrl+C
        print('\nGrader was stopped with Ctrl+C')


if __name__ == '__main__':
    start()
