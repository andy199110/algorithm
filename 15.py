# -*- coding:utf-8 -*-
__author__ = 'Administrator'


#coding: utf-8

def run():
    print("hello")


if __name__ == "__main__":
    run()

import pandas as pd
import numpy as np
import quandl
import tushare


def initialize(context):
    g.choicenum = 7  # 预选小市值股票数
    g.days = 0  # 计时器
    g.period = 13  # 调仓频率
    g.openorder = []  # 未能成功清仓的股票名


def before_trading_start(context):
    # 今天是否运行
    g.run_today = g.days % g.period == 0
    if g.run_today:
        # 设置沪深两市所有股票为股票池
        scu0 = get_index_stocks('000001.XSHG')
        scu3 = get_index_stocks('399001.XSHE')
        scu = scu0 + scu3
        set_universe(scu)


def handle_data(context, data):
    # 调仓日交易
    if g.run_today:
        # 每天只运行一次
        g.run_today = False

        date = context.current_dt.strftime("%Y-%m-%d")
        buylist = []

        # 清空未完成订单
        for stock in g.openorder:
            order_target(stock, 0)
        g.openorder = []

        # 选出低市值的股票，buylist
        df = get_fundamentals(query(
            valuation.code, valuation.market_cap
        ).filter(
            valuation.code.in_(context.universe)
        ).order_by(
            valuation.market_cap.asc()
        ).limit(g.choicenum), date=date
                              ).dropna()
        buylist = list(df['code'])

        # 目前持仓中不在buylist中的股票，清仓
        for stock in context.portfolio.positions:
            if stock not in buylist:
                order_target(stock, 0)

        # 等权重买入buylist中的股票
        position_per_stk = context.portfolio.cash / g.choicenum
        for stock in buylist:
            if not data[stock].isnan():
                amount = int(position_per_stk / data[stock].price)
                order(stock, +amount)

    # 获得每天未成功卖单股票
    orders = get_open_orders()
    g.openorder += [t.security for t in orders if not t.is_buy]

    # 天数加一
    g.days += 1