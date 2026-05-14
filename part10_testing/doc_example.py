from functools import reduce
from operator import mul


def multiply_numbers(*args):
    """
    Вычисляет произведение позиционных аргументов.

    >>> multiply_numbers(2, 4, 3)
    24
    >>> multiply_numbers(1, 2)
    100
    """
    return reduce(mul, args)
