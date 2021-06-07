import random
import testing_tools as tt


def check_inout(code):
    # Объявляем корректное решение
    def solution(user_in):
        total_sec = int(user_in)
        hours = total_sec // 3600
        minutes = (total_sec // 60) % 60
        seconds = total_sec % 60
        return '{}:{}:{}'.format(hours, minutes, seconds)

    # Создаем тестовые значения
    test_values = ['0', '1']
    while len(test_values) < 10:
        new = str(random.randint(0, 86000))
        if new not in test_values:
            test_values.append(new)

    # Сравниваем код решения пользователя с корректным решением
    return tt.test_input_print(code=code, values=test_values, solution=solution)
