
# -*- coding:utf-8 -*-
__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()
import math

def time(n):
    """ Return the number of steps
    necessary to calculate
    `print countdown(n)`"""
    return 3+2*math.ceil(n/5)
    # YOUR CODE HERE


def countdown(x):
    y = 0
    while x > 0:
        x = x - 5
        y = y + 1
    print y

print time(50)