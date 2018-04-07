# -*- coding:utf-8 -*-
__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()
import tushare as ts
hq=ts.get_day_all()
shares=ts.get_stock_basics()
hq=hq.set_index('code')
basics=shares[['resevedPerShare','esp','timeToMarket']]
df=hq.merge(basics,left_index=True,right_index=True)
print df