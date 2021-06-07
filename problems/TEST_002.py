import testing_tools as tt

def check(code):
    # Проверяем объявил ли пользователь переменную "answer"
    try:
        answer = code.answer
    except AttributeError:
        return {'correct': False, 'error': 'variable ({}) is not defined.'.format('answer')}

    # Переменная "expected" содержит правильное решение
    expected = [1, 2, 3, 4, 5]

    # Сравниваем содержимое переменной "answer" и "expected" при помощи вспомогательной тестовой функции
    return tt.test_variable(answer=answer, expected=expected)
