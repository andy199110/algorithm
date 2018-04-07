# -*- coding:utf-8 -*-
__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()
def rerussian(a,b):
    if a==0:return 0
    if a%2==0:return 2*rerussian(a/2,b)
    return b+2*rerussian((a-1)/2,b)
print rerussian(100,10)