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
from numba import jit
import time

#单支股票提示买卖点

#  single_share=ts.get_hist_data('000908',start='2018-03-02',end='2018-04-05',ktype='30')#获取股票30分钟数据
# fenshi=pd.DataFrame.as_matrix(single_share)#数据处理
# share_close=fenshi[:,2]#收盘价
# share_ma20=fenshi[:,9]#20均价
# for i in range(len(share_close)-1):
#     if share_close[i+1]<share_ma20[i+1] and share_close[i]>=share_ma20[i]:
#         print ('buy'+str(i))
#     elif share_close[i+1]>share_ma20[i+1] and share_close[i]<=share_ma20[i]:
#         print ('sell'+str(i))
# print single_share

#所有股票筛选

#1.根据pe和流通值筛选
# all_share=ts.get_day_all()#获取所有股票数据
# all_share_pd=pd.DataFrame(data=all_share)#数据转格式
#all_share.to_csv('D:/python code/algorithm/1.csv')#保存数据为csv文件
all_share_name=pd.read_csv('D:/python code/algorithm/1.csv')#从csv文件中调取数据
all_share_name=all_share_name.as_matrix()#数据转矩阵格式
buy_list_fr=[]#初始化股票池
all_share_name_1=np.array(all_share_name[:,1])#表示股票代码矩阵
pd.DataFrame(all_share_name[:,10]).to_csv('D:/python code/algorithm/3.csv')#保存pe数据为csv格式
print all_share_name[:,10]
for i in range(3512):#3512根据股票数确定
    if all_share_name[i,12]==0:#排除分母为0的情况
        continue
    elif int(all_share_name[i,10])<=200 and int(all_share_name[i,10])>-30 and all_share_name[i,14]*all_share_name[i,4]/all_share_name[i,12]<200000:#根据pe和流通量筛选
        print all_share_name[i,14]*all_share_name[i,4]/all_share_name[i,12]#流通股本的表示
        buy_list_fr=np.append(buy_list_fr,str(all_share_name_1[i]))#将符合条件的股票加入股票池
    else:
        continue
print buy_list_fr

#2补充股票代码缺失

# tansfome code to six
for i in range(len(buy_list_fr)):
    # if len(str(all_share_name[i]))==1:
    #     all_share_name[i]='00000'+str(all_share_name[i])
    # elif len(str(all_share_name[i]))==2:
    #     all_share_name[i] = '0000' + str(all_share_name[i])
    # elif len(str(all_share_name[i]))==3:
    #     all_share_name[i] = '000' + str(all_share_name[i])
    # elif len(str(all_share_name[i]))==4:
    #     all_share_name[i] = '00' + str(all_share_name[i])
    # elif len(str(all_share_name[i]))==5:
    #     all_share_name[i] = '0' + str(all_share_name[i])
    # else:
    #     all_share_name[i] =  str(all_share_name[i])
    buy_list_fr[i]='0'*(6-len(str(buy_list_fr[i])))+str(buy_list_fr[i])#补代码缺失
# all_share_name=pd.read_csv('D:/python code/algorithm/2.csv')
# all_share_name=pd.DataFrame.as_matrix(all_share_name)
#get buy code
# t=time.localtime()
# a=0
print buy_list_fr

#3.根据股价是否上穿20均线选股

buy_list=[]
# while (t [3]<8 or t[4]<55):
#     for i in range(len(all_share_name)):
#         #print all_share_name[i]
#         all_to_single_share = ts.get_hist_data(all_share_name[i], start='2018-03-02', end='2018-04-05', ktype='30')
#         #print all_to_single_share
#         all_to_single_fenshi = pd.DataFrame(data=all_to_single_share)
#         #print all_to_single_fenshi
#         all_to_single_fenshi=all_to_single_fenshi.as_matrix()
#         #share_time = all_to_single_share.index
#
#         #print share_close
#         if len(all_to_single_fenshi)<2 :
#             continue
#         else:
#             share_close = all_to_single_fenshi[:, 2]
#             share_ma20 = all_to_single_fenshi[:, 9]
#             if share_close[2]<share_ma20[2] and share_close[1]>=share_ma20[1]:
#                buy_list.append(all_share_name[i])
#                print buy_list
for i in range(len(buy_list_fr)):
     # print all_share_name[i]
     all_to_single_share = ts.get_hist_data(buy_list_fr[i], start='2018-03-20', end='2018-04-04',ktype='30')#获取股票30分钟数据
     # print all_to_single_share
     all_to_single_fenshi = pd.DataFrame(data=all_to_single_share)
      # print all_to_single_fenshi
     all_to_single_fenshi = all_to_single_fenshi.as_matrix()#数据转矩阵
     # share_time = all_to_single_share.index

     # print share_close
     if len(all_to_single_fenshi) < 2:#排除数据缺失的情况
         continue
     else:
         # share_close = all_to_single_fenshi[:, 2]
         # share_ma20 = all_to_single_fenshi[:, 9]
         if all_to_single_fenshi[3,2] < all_to_single_fenshi[3,9] and all_to_single_fenshi[2,2] < all_to_single_fenshi[2,9] and all_to_single_fenshi[1,2] <= all_to_single_fenshi[1,9] and all_to_single_fenshi[0,2] >= all_to_single_fenshi[0,9]:#判断股价是否上穿20均线
             buy_list.extend([buy_list_fr[i]])#将符合条件股票加入股票池
print buy_list
buy_list=np.array(buy_list).T
# buy_list.to_csv('D:/python code/algorithm/2.csv')
# buy_list=pd .read_csv('D:/python code/algorithm/2.csv')

#4.根据流通值选股，与前面重复
buy_list_se=[]
for i in range(len(buy_list)):
    single_share1 = ts.get_hist_data(code=buy_list[i])
    single_share = pd.DataFrame(single_share1)
    single_share=single_share.as_matrix()
    if len(single_share)<13:
        continue
    else:
        circulating_market_cap=single_share[0,4]*single_share[0,2]/single_share[0,13]
    # circulating_market_cap = single_share[0, 4] * single_share[0, 2] / single_share[0, 13]
    if circulating_market_cap<=200000:
        buy_list_se=np.append(buy_list_se,buy_list[i])
print buy_list_se
    #a=a+1
    #t = time.localtime()

# print t
# print a

# print str(all_share_name)