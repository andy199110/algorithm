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
from numba import vectorize
import time

all_share_name=['603316','603617','603536','603041','603331','603196','002905','000004']
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
@jit
def buylist(allcode):
    for i in range(len(allcode)):
     # print all_share_name[i]
         all_to_single_share = ts.get_hist_data(allcode[i], start='2018-04-02', end='2018-04-04',ktype='60')

         print all_to_single_share
         all_to_single_fenshi = pd.DataFrame(data=all_to_single_share)
      # print all_to_single_fenshi
         all_to_single_fenshi = all_to_single_fenshi.as_matrix()
     # share_time = all_to_single_share.index
         print all_to_single_fenshi[:, 9]

     # print share_close
         if len(all_to_single_fenshi) < 2:
             continue
         else:
         # share_close = all_to_single_fenshi[:, 2]
         # share_ma20 = all_to_single_fenshi[:, 9]
             if all_to_single_fenshi[1,2] < all_to_single_fenshi[1,9] and all_to_single_fenshi[0,2] >= all_to_single_fenshi[0,9]:
                buy_list.append(all_share_name[i])
    return buy_list
buy_list=buylist(all_share_name)
print buy_list
buy_list=np.array(buy_list).T
# buy_list.to_csv('D:/python code/algorithm/2.csv')
# buy_list=pd .read_csv('D:/python code/algorithm/2.csv')


@jit
def butlist_se(code_se):
    buy_list_se = []
    for i in range(len(code_se)):
         single_share1 = ts.get_hist_data(code=code_se[i])
         single_share = pd.DataFrame(single_share1)
         single_share=single_share.as_matrix()
         if len(single_share)<13:
            continue
         else:
            circulating_market_cap=single_share[0,4]*single_share[0,2]/single_share[0,13]
    # circulating_market_cap = single_share[0, 4] * single_share[0, 2] / single_share[0, 13]
         if circulating_market_cap<=200000:
            buy_list_se=np.append(buy_list_se,buy_list[i])
    return buy_list_se
buy_list_se=butlist_se(buy_list)
print buy_list_se
    #a=a+1
    #t = time.localtime()

# print t
# print a

# print str(all_share_name)