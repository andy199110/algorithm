# -*- coding:utf-8 -*-
__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()
def naive(a, b):
    x = a
    y = b
    z = 0
    while x > 0:
        z = z + y
        x = x - 1
    return z

def time(a):
    # The number of steps it takes to execute naive(a, b)
    # as a function of a

    # your code here
    return 2*a+3