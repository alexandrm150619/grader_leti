import random
import testing_tools as tt


def check(code):
    # Провеяем создал ли пользователь функцию "sum"
    try:
        function = code.sum
    except AttributeError:
        return {'correct': False, 'error': 'function ({}) is not defined.'.format('sum')}

    # Создаем функцию "solution", которая является корректным решением
    def solution(x, y):
        return x + y

    # Используем 5 заранее заданных и 5 сгенерированных тестовых значений
    test_values = [(0, 0), (0, 1), (1, 0), (-1, 0), (0, -2)]
    while len(test_values) < 10:
        new = (random.randint(-1000, 1001), random.randint(-1000, 1001))
        if new not in test_values:
            test_values.append(new)

    # Сравниваем пользовательский код и корректное решение
    return tt.test_function(function=function, values=test_values, solution=solution)
