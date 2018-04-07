# -*- coding:utf-8 -*-
__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()
import tushare as ts
import pandas as pd
import numpy as np
import xlwt
import xlrd
all_share_name=pd.read_csv('D:/python code/algorithm/1.csv')
all_share_name=all_share_name.as_matrix()
all_share_name=all_share_name[:,1]
for i in range(len(all_share_name)):
    all_share_name[i] = '0' * (6 - len(str(all_share_name[i]))) + str(all_share_name[i])
all_share_name=pd.DataFrame(all_share_name)
all_share_name.to_csv('D:/python code/algorithm/2.csv')
