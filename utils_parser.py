from constants import *


def preprocess_number(number):
    number = str(number)
    number = number.replace("-", " ")
    return number
