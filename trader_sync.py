# -*- coding: utf-8 -*-
'''
By:晚起的小虫
version: bata 1.0.14
------------------------------------
1.0.14 更新：
    修正获取可用资金，总资产时的潜在BUG。
1.0.13 更新：
            新增 TraderOrder类 为订单返回结构，定义参考自 聚宽的Order对象
    ShipaneTrader order返回为与JoinQuant一样的Order结构。这里因同步采用五档成交剩即撤方式同步的，故只做简化order返回，没有考虑限价单的返回。
    TraderSynchronizer 下单结果判断更改为按order判断，不再根据异常判断。下单成功与否以order.filed > 0来判断
    YH_EasyTrader与RichQuantTrader未实现返回order结构。
此功能为统一订单返回，更方便不同交易盘之间的同步。
------------------------------------
持仓同步为一个以源交易盘为准，对比目标交易盘的持仓，获取差值。再通过下卖单，买单，使之持仓与源交易盘相同或尽量相同。
以 聚宽->实盘易 为例
源交易盘     : 聚宽模拟盘
目标交易盘 : 实盘易操控的券商通达信
该方法优点：
1.在资金量相差不大的情况下。尽量使之实盘持仓与模拟盘相同，使策略与实盘偏差变小，易于验证策略有效性，减少实盘持仓误差对策略有效性的干扰。
2.自动对比持仓决定下单量，意味着假如一次操作失败，下次同步依然会尽量保持相同持仓。容错好。
该方法缺点：
1.只能使用在一个策略对一个券商号的情况。
2.源交易盘资金量大于目标交易盘过多时，可能会导致目标交易盘买股不足，最终导致 频繁的调仓，此时要设置正确的 实盘/模拟盘 资金比
--------------------------------------------------------------------------------------------
'''
'''
聚宽->实盘易 同步示例代码:

from trader_sync import *    # 导入持仓同步库

# 定义一个不参与同步的股票名单。(防打新中签后被卖，该函数建议定义在另外的.py文件，更改时就无需更新模拟盘代码)
def get_white_list():
    return []

# 聚宽初始化
def initialize(context):
    # 指定实盘易返回各字段名，以下为通达信模拟交易字段(招商证券，广发证券也一致)。注：未来版本实盘易可能会返回统一的字段名，各券商无需再指定
    col_names = {
            '可用':u'可用','市值':u'参考市值'
            ,'证券代码':u'证券代码','证券数量':u'证券数量','可卖数量':u'可卖数量','当前价':u'当前价','成本价':u'成本价'
            }
    # ******** 创建持仓同步器 **********
    g.sync_p = JoinQuantSyncPosition(
        host = '111.111.111.111'       # 实盘易参数，目标交易盘易IP,必写                                                                                                                                           默认:
        ,port = 8888                   # 实盘易参数，目标交易盘易端口                                                                                                                                                    默认:8888
        ,key = ''                      # 实盘易参数，目标交易盘易Key                                                 默认:
        ,client = 'title:moni'         # 实盘易参数，目标交易盘易操作的券商标识                                                                                                                                默认: 
        ,strong_op = True              # 同步器参数，强力买卖操作模式,该模式下，会先对比持仓卖一次买一次，再对比持仓再卖一次买一次                         默认: False
        ,check_run_time = True         # 同步器参数，检测运行时间，设置为True，则回测时不会同步持仓,                           默认: True
        ,get_white_list_func = get_white_list # 同步器参数，获取不同步的股票列表的函数。注意不能赋与另一个对象的方法，会序列化失败的。     默认: None
        ,sync_scale = 1.0              # 该值意指 实盘/模拟盘的资产比例。 假如模拟盘100W，实盘50W，则设置为0.5                   默认: 1.0 
                                       # 使用比例后，取整是四舍五入，结果就是买会少买，卖会少卖，
                                       # 例如 模拟盘比例缩放后 640股，实盘0股，则买入600股。模拟盘640股，实盘1000股，则只卖300股。当然若模拟盘0股，则实盘全清
        ,col_names = col_names         # 同步器参数，指定实盘易查询持仓时，返回的各个要使用到的字段名                                                                                                                 
                                       # 默认: {'可用':u'可用','市值':u'参考市值'
                                       #        ,'证券代码':u'证券代码','证券数量':u'证券数量','可卖数量':u'可卖数量'
                                       #        ,'当前价':u'当前价','成本价':u'成本价'}
        )

def handle_data(context,data):
    # 这里写策略代码
    #
    # ...
    
    order('000001.SXHE',1000) # 交易示例    
    # ******** 调用同步,应在聚宽该时间下调仓全部完成后，或清仓后执行同步 **********
    g.sync_p.execute(context,data) # 如果没有 data 可写 g.sync_p.execute(context,None)
--------------------------------------------------------------------------------------------
'''
'''
实现代码，各类作用说明:
1.基础数据类：
    TraderPosition           定义一只股票的仓位信息        参考 聚宽的context.portfolio.position
    TraderPortfolio          定义股票持仓信息                    参考 聚宽的 context.portfolio
    TraderSecurityUnitData   定义股票的价格信息类，        参考  聚宽的 data
    TraderOrder              定义订单返回结果                    参考  聚宽的Order对象
2.交易盘类:
    TraderBase               交易盘虚类，约定统一接口。1)获取持仓数据     2)交易     3)获取价格、时间等信息。
        ShipaneTrader        实盘易    交易盘实现
        YH_EasyTrader        Easytrader    银河交易盘实现(未完成)
        JoinQuantTrader      聚宽    交易盘实现 
        RichQuantTrader      米筐    交易盘实现(未完成)
3.两个交易盘的同步器 ****:
    TraderSynchronizer       交易盘同步器
4.持仓同步的再次封装类:
    JoinQuantSyncPosition    聚宽->实盘易 的同步封装类。方便调用。
-------------------------------------------------------------------------------------------
'''

import datetime as dt
from math import *
import time


# ===以聚宽的定义为模板，定义股票的持仓数据类。===
# ''' 定义一只股票的持仓数据 '''
class TraderPosition(object):
    def __init__(self, **kwargs):
        self.security = kwargs.get('security', None)  # 股票代码
        self.price = kwargs.get('price', None)  # 最新行情价格
        self.avg_cost = kwargs.get('avg_cost', self.price)  # 成本
        self.total_amount = kwargs.get('total_amount', None)  # 总仓位, 但不包括挂单冻结仓位
        self.closeable_amount = kwargs.get('closeable_amount', None)  # 可卖出的仓位
        self.stock_name = kwargs.get('stock_name', None)  # 证券名称

    def __str__(self):
        return '[股票:%s 当前价:%.2f 成本:%.2f 持仓数:%d 可卖数:%d]' % (self.security
                                                           , self.price, self.avg_cost, self.total_amount,
                                                           self.closeable_amount)


# ''' 定义持仓数据 '''
class TraderPortfolio(object):
    def __init__(self):
        self.available_cash = None  # 可用资金, 可用来购买证券的资金
        self.positions_value = None  # 持仓价值
        self.positions = {}  # 持仓 key为股票代码，TraderPosition
        self.subportfolios = [self.positions]  # 子仓0 即主仓
        self._total_values = None

    def __str__(self):
        ps = [str(p) for p in self.positions.values()]
        return '[可用资金:%.2f] [市值:%.2f] [持仓：%s]' % (self.available_cash, self.positions_value, ','.join(ps))

    @property
    def long_positions(self):
        return self.positions

    @property
    def total_values(self):
        try:
            if self._total_values == None:
                return self.positions_value + self.available_cash
            else:
                return self._total_values
        except:
            return self.positions_value + self.available_cash


# ''' 股票价格信息 '''
class TraderSecurityUnitData(object):
    def __init__(self, **kwargs):
        self.price = kwargs.get('price', 0)  # 当前价
        self.high_limit = kwargs.get('high_limit', 0)  # 涨停价
        self.low_limit = kwargs.get('low_limit', 0)


try:
    from enum import Enum


    # ''' 订单状态  与聚宽定义相同 '''
    class OrderStatus(Enum):
        # 订单未完成, 无任何成交
        open = 0
        # 订单未完成, 部分成交
        filled = 1
        # 订单完成, 已撤销, 可能有成交, 需要看 Order.filled 字段
        canceled = 2
        # 订单完成, 交易所已拒绝, 可能有成交, 需要看 Order.filled 字段
        rejected = 3
        # 订单完成, 全部成交, Order.filled 等于 Order.amount
        held = 4
except:
    def enum(**enums):
        return type('Enum', (), enums)


    OrderStatus = enum(open=0, filled=1, canceled=2, rejected=3, held=4)


# ''' 下单返回  与聚宽定义相同'''
class TraderOrder(object):
    def __init__(self):
        self.status = OrderStatus.open
        self.add_time = None
        self.is_buy = True
        self.amount = 0
        self.filled = 0
        self.security = ''
        self.order_id = 0
        self.price = 0
        self.avg_cost = 0
        self.side = 'long'
        self.action = 'open'

    def __str__(self):
        return 'action: %s filled : %d status:%s' % (self.action, self.filled, self.status)


# ''' 定义交易者,虚类 '''
class TraderBase(object):
    # 为适应各平台，传入context和data方便最终调用。
    def __init__(self):
        self.context = None
        self.data = None

    # 持仓数据
    @property
    def portfolio(self):
        return TraderPortfolio()

    # 当前时间，用于检测下单是否有效
    @property
    def current_dt(self):
        return dt.datetime.now()

    # 下单，子类实现时，下单失败应该返回一个异常！
    def order(self, **kwargs):
        raise Exception('未实现order')

    # 获取一只股票的价格信息
    def get_data(self, stock):
        return TraderSecurityUnitData(price=None, high_limit=None)

    def login(self):
        pass


# '''----交易盘同步器，以source_trader为准，把dest_trader的持仓调整到与source_trader尽量一致------ '''
class TraderSynchronizer(object):
    def __init__(self, logger, source_trader, dest_trader, **kwargs):
        self._logger = logger
        self._source_trader = source_trader  # 源交易盘
        self._dest_trader = dest_trader  # 目标交易盘
        self._strong_op = kwargs.get('strong_op', True)  # 开启强力同步模式
        self._check_run_time = kwargs.get('check_run_time', True)  # 检测运行时间，设置为True，则回测时不会同步持仓
        self._i_code, self._i_amount, self._i_closeable_amount = range(3)  # 持仓二维数组操作索引
        self.normalize_code = kwargs.get('normalize_code', my_normalize_code)  # 默认规整股票代码的方法
        self._expire_before = dt.datetime.combine(dt.date.today(), dt.time.min)  # 有效起点时间
        self.__order_list = []  # 保存实盘同步时操作成功的股票和数量List，每次同步前自动清空
        self._get_white_list_func = kwargs.get('get_white_list_func', None)
        self.__sync_scale = kwargs.get('sync_scale', 1.0)  # 实盘/模拟盘总资金

    # 将目标交易盘与源交易盘同步调用的方法。源交易盘调完仓或清仓后调用。返回目标盘操作成功的代码及股数
    def execute(self, context, data):
        self.__order_list = []
        # 保存源数据，方便调用
        self._source_trader.context = context
        self._dest_trader.context = context
        self._source_trader.data = data
        self._dest_trader.data = data
        # 检测源交易盘的时间
        if self._check_run_time and self._source_trader.current_dt < self._expire_before:
            self._logger.info('[交易盘同步器] 执行同步时间不正确，忽略同步请求')
            return
        self._source_trader.login()
        self._dest_trader.login()
        try:
            # 通过对比持仓获得要操作的股票及数量
            sell_list, buy_list = self._get_position_variance()
            if len(sell_list) + len(buy_list) == 0:
                self._logger.info('[交易盘同步器] 源交易盘与目标交易盘持仓一致，无需调仓。')
                return
            self._sell(sell_list)
            self._buy(buy_list)
            if self._strong_op:
                sell_list, buy_list = self._get_position_variance()
                # 强力买卖条件下,卖两次股,防止五档都没卖掉或者网络错误,扫两次五档没卖完就算了吧
                self._sell(sell_list)
                # 强力买卖条件下,买股,买两遍，第一遍为买，第二遍为检查，防止部分五档扫完还没买够的,或者网络错误
                self._buy(buy_list)
        except Exception as e:
            self._logger.error('[交易盘同步器] 对比持仓执行错误:' + str(e))
        # 用完释放
        self._source_trader.context = None
        self._dest_trader.context = None
        self._source_trader.data = None
        self._dest_trader.data = None
        self._logger.info(
            '[交易盘同步器] 本次交易汇总:\n' + '\n'.join(['[%s : %d]' % (stock, amount) for stock, amount in self.__order_list]))
        return self.__order_list

    # 获取源交易盘总资产-目标交易盘总资产的资金差额
    def difference_cash(self, context, data):
        self._source_trader.context = None
        self._dest_trader.context = None
        self._source_trader.data = None
        self._dest_trader.data = None
        return (self._source_trader.portfolio.available_cash
                + self._source_trader.portfolio.positions_value
                - self._dest_trader.portfolio.positions_value
                - self._dest_trader.portfolio.available_cash)

    # 卖股
    def _sell(self, op_list):
        self._logger.info('[交易盘同步器] 目标卖股:' + str(op_list))
        for stock, amount, closeable_amount in op_list:
            if closeable_amount <= 0:
                self._logger.info('[交易盘同步器] 目标卖股 %s 可卖数量不足!:' % (stock))
                continue
            amount = abs(amount)
            if amount != closeable_amount:  # 目标数量与可卖数量不相等，则取 目标数量和可卖数量的最小值，并截取整数
                sell_count = trunc_amount(min(amount, closeable_amount))
            else:
                sell_count = amount

            order = self._dest_trader.order(action='SELL', symbol=stock
                                            , type='MARKET', priceType=4, amount=sell_count)
            if order.filled > 0:
                self._logger.info('[交易盘同步器] 卖单成功! [%s : %d]' % (stock, sell_count))
                self.__order_list.append([stock, -sell_count])
            else:
                self._logger.error("[交易盘同步器] 卖单失败  [%s : %d]" % (stock, sell_count))

    # 买股
    def _buy(self, op_list):
        self._logger.info('[交易盘同步器] 目标买股:' + str(op_list))

        cash = self._dest_trader.portfolio.available_cash
        # 买股
        for stock, amount, closeable_amount in op_list:
            buy_count = abs(amount)
            # ===买单时需要获取实际资金，以涨停价计算最大挂单数买入。===
            # ===最后一单经常需要拆成两单买入。还有误差就不管了。===
            high_limit = self._source_trader.get_data(stock).high_limit
            price = self._source_trader.get_data(stock).price
            if high_limit == None:  # 如果从源交易盘获取最高价失败，则从目标交易盘获取
                high_limit = self._dest_trader.get_data(stock).high_limit
                price = self._dest_trader.get_data(stock).high_limit

            if high_limit == None or high_limit == 0:
                self._logger.error('[交易盘同步器] 买单异常 [%s : %d] 获取股票涨停价失败！' % (stock, buy_count))
                continue

            # 为防最后一单 买单 ，因通达信用涨停价计算最大可买数量，与实际成交所需资金的差异，所以尝试多次交易，尽量达到目标
            # 为减少查询实盘的可用资金次数，这里进行模拟计算花费了多少可用资金
            for i in range(3):
                if i > 0:  # 同一支股票，进行第二次再买时，从实盘查询资金
                    cash = self._dest_trader.portfolio.available_cash

                # 获取目标交易盘可用资金
                if cash == None:
                    self._logger.error('[交易盘同步器] 买单异常 [%s : %d] 获取可用资金失败' % (stock, buy_count))
                    break
                # 计算当前可用资金以涨停价挂单的最大挂单数
                max_count = trunc_amount(cash / high_limit)
                self._logger.info('[交易盘同步器] %d 次买计算:[股票 : %s][涨停价:%f] [可用资金: %f] [最多可买:%d] [目标:%d]' % (
                    i + 1, stock, high_limit, cash, max_count, buy_count))
                if max_count <= 0:
                    self._logger.warning('[交易盘同步器] 买单失败 [%s : %d] 可用资金不足' % (stock, buy_count))
                    break
                # 取目标数量与最大数量的最小值去下单
                to_buy_count = min(max_count, buy_count)
                order = self._dest_trader.order(action='BUY', symbol=stock
                                                , type='MARKET', priceType=4, amount=to_buy_count)
                if order.filled > 0:
                    self._logger.info('[交易盘同步器] 买单 成功 [%s : %d]' % (stock, to_buy_count))
                    self.__order_list.append([stock, to_buy_count])
                    if i == 0:  # 股票第一次买入时，虚拟计算资金即可，减少从实盘查询资金的次数。
                        cash -= price * to_buy_count * 1.005  # 多计算0.5%，以防价格波动太厉害。
                    buy_count -= to_buy_count
                    # 买完
                    if buy_count <= 0:
                        break
                else:
                    self._logger.error("[交易盘同步器] 买单失败  [%s : %d]" % (stock, buy_count))

    # 获取交易盘持仓，二维数组 [[股票代码，持仓数，可卖数],[股票代码，持仓数，可卖数]]
    def _get_trader_positions_list(self, trader):
        r = trader.portfolio
        trader_p_l = [[p.security, p.total_amount, p.closeable_amount] for p in r.positions.values()]
        # 对可卖数量与持仓不一致的股票的可卖数量进行100取整，避免下单时数量不凑手
        trader_p_l = [[self.normalize_code(stock),
                       int(amount),
                       closeable_amount if amount == closeable_amount else trunc_amount(closeable_amount)
                       ]
                      for stock, amount, closeable_amount in trader_p_l]
        # 过滤掉那些外部定义不需要进行同步的股票
        if self._get_white_list_func != None:
            try:  # 这里Try一下，避免外部函数有问题导致程序崩溃
                out_of_sync_stock_list = self._get_white_list_func()
                out_of_sync_stock_list = [self.normalize_code(stock) for stock in out_of_sync_stock_list]
            except Exception as e:
                self._logger.error('获取不同步的股票白名单错误:' + str(e))
                out_of_sync_stock_list = []
        else:
            out_of_sync_stock_list = []
        return [x for x in trader_p_l if x[self._i_amount] != 0 and x[self._i_code] not in out_of_sync_stock_list]

    # 获取两持仓之差,返回一个[[股票代码,买卖amount,dest_trader可卖数量],[股票代码,买卖amount,dest_trader可卖数量]]的二维数组
    def _get_position_variance(self):
        # 获取源交易盘持仓 [股票代码,持仓数,可卖数量]的 二维数组
        source_p_l = self._get_trader_positions_list(self._source_trader)
        self._logger.info('[交易盘同步器] 源交易盘持仓:', source_p_l)

        # 获取目标交易盘总持仓 [股票代码,持仓数,可卖数量] 的二维数组
        dest_p_l = self._get_trader_positions_list(self._dest_trader)
        self._logger.info('[交易盘同步器] 目标交易盘持仓:', dest_p_l)

        # 规整数据，把目标交易盘的持仓数量变为负的，以便sum来统计差异量。
        dest_p_l = [[self.normalize_code(stock), -amount, closeable_amount]
                    for stock, amount, closeable_amount in dest_p_l]
        # 规整数据，为源交易盘持仓第三列可卖数量设置为0,方便计算。按比例缩放源交易盘持仓量
        try:
            self.__sync_scale
        except:
            self.__sync_scale = 1
        source_p_l = [[self.normalize_code(stock), int(amount * self.__sync_scale), 0] for
                      stock, amount, closeable_amount in source_p_l]
        all_p_l = source_p_l + dest_p_l
        # 获取所有不重复的股票代码
        stock_list = list(set([stock for stock, amount, closeable_amount in all_p_l]))
        # 取两个列表之差异
        dif_list = [
            [stock_code, sum([amount for stock, amount, closeable_amount in all_p_l if stock == stock_code])
                , sum([closeable_amount for stock, amount, closeable_amount in all_p_l if stock == stock_code])
             ]
            for stock_code in stock_list
        ]
        dif_list = [x for x in dif_list if x[self._i_amount] != 0]
        self._logger.info('[交易盘同步器] 持仓差异:', dif_list)
        # 对数据进行股票数量的按手规整
        results = []
        for stock, amount, closeable_amount in dif_list:
            # 若amount已经为100的整数得直接添加 。
            if amount % 100 == 0:
                results.append([stock, amount, closeable_amount])
                continue

            # 不是整手的股票处理。
            if amount < 0:
                # ===只判断amount的合理性，未结合closeable_amount判断。交易下单时和结合closeable_amount判断
                # ===卖股，可卖数量与持仓数量一致的情况下，才能返回非整手的可卖数。
                # 取源交易盘的持仓量
                t = [x[self._i_amount] for x in source_p_l if x[self._i_code] == stock]
                if len(t) == 0 or t[0] == 0:
                    # 如果源交易盘已清仓该股，则目标交易盘全卖
                    results.append([stock, amount, closeable_amount])
                else:
                    # 源交易盘未清仓的，则对股票数量取整
                    results.append([stock, trunc_amount(amount), closeable_amount])
            else:
                # 买股直接对数量进行四舍五入取整
                results.append([stock, round_amount(amount), closeable_amount])
        # 拆分返回卖股列表和买股列表
        sell_list = [x for x in results if x[self._i_amount] < 0]
        buy_list = [x for x in results if x[self._i_amount] > 0]
        return sell_list, buy_list


'''--------------------------一些要用到的函数-------------------'''
import re


# 从各种不同的股票代码表达方式中解析出统一的 6位数字组成的字符串的股票代码。
def my_normalize_code(stock):
    try:
        return re.search(r'[^\d]*(\d{6})[^\d]*', stock.encode('utf-8')).group(1)
    except:
        raise Exception('非法代码格式')


# 对股票进行整手截整 买股 105返回 100，卖股 -105返回100
def trunc_amount(amount):
    return trunc(abs(amount) / 100) * 100 if amount > 0 else -trunc(abs(amount) / 100) * 100


# 四舍五入取整手数
def round_amount(amount):
    return int(round(amount * 1.0 / 100) * 100)


'''---------------------------实盘易 交易盘类--------------------'''
try:
    import shipane_sdk
except:
    print '未发现 shipane_sdk'
    pass


def get_shipane_deault_col_name():
    return {
        '可用': u'可用', '市值': u'参考市值', '证券名称': u'证券名称', '资产': u'资产'
        , '证券代码': u'证券代码', '证券数量': u'证券数量', '可卖数量': u'可卖数量', '当前价': u'当前价', '成本价': u'成本价'
    }


# ''' 实盘易 交易盘 '''
class ShipaneTrader(TraderBase):
    def __init__(self, logger, **kwargs):
        TraderBase.__init__(self)
        self._logger = logger
        self._client = shipane_sdk.Client(self._logger, **kwargs)
        self._client_param = kwargs.get('client', '')
        self._auto_restart_shipane = kwargs.get('auto_restart_shipane', False)
        self._col_names = kwargs.get('col_names', get_shipane_deault_col_name())
        try:
            self._col_names['证券名称']
        except:
            self._col_names['证券名称'] = u'证券名称'

    @property
    def portfolio(self):
        try:
            self._col_names
        except:
            self._col_names = get_shipane_deault_col_name()
        pf = TraderPortfolio()
        r = self.__get_sp_response()
        try:
            pf.available_cash = float(r['sub_accounts'][self._col_names['可用']][u'人民币'])
        except:
            pf.available_cash = float(r['sub_accounts'][self._col_names['可用']])
        try:
            pf.positions_value = float(r['sub_accounts'][self._col_names['市值']][u'人民币'])
        except:
            pf.positions_value = float(r['sub_accounts'][self._col_names['市值']])
        try:
            pf._total_values = float(r['sub_accounts'][self._col_names['资产']][u'人民币'])
        except:
            pf._total_values = float(r['sub_accounts'][self._col_names['资产']])
            pass
        positions = r['positions']
        sp = zip(positions[self._col_names['证券代码']], positions[self._col_names['证券名称']],
                 positions[self._col_names['证券数量']]
                 , positions[self._col_names['可卖数量']], positions[self._col_names['当前价']],
                 positions[self._col_names['成本价']])
        sp = [[stock, stock_name, int(float(amount)), int(float(closeable_amount)), float(price), float(avg_cost)]
              for stock, stock_name, amount, closeable_amount, price, avg_cost in sp
              if stock != '' and amount != '' and closeable_amount != '' and price != '' and avg_cost != '']
        for stock, stock_name, amount, closeable_amount, price, avg_cost in sp:
            pf.positions[stock] = TraderPosition(security=stock.encode('utf-8')
                                                 , stock_name=stock_name
                                                 , total_amount=amount
                                                 , closeable_amount=closeable_amount
                                                 , price=price
                                                 , avg_cost=avg_cost)

        return pf

    # 下单，规整为统一类型的下单返回未实现
    def order(self, **kwargs):
        self._last_order_time = dt.datetime.now()
        result = TraderOrder()
        try:
            if kwargs['action'] == 'BUY':
                result.action = 'open'
                result.is_buy = True
            else:
                result.action = 'close'
                result.is_buy = 'False'
            result.amount = kwargs['amount']
            self._client.execute(self._client_param, **kwargs)
            # 这里简化处理，如果订单没有异常，就认为全部成交。
            result.filled = result.amount
            result.status = OrderStatus.held
        except Exception as e:
            self._logger.error('[实盘易] 订单异常:' + str(e))
            # 这里简化处理，订单异常则认为没有成交
            result.filled = 0
            result.status = OrderStatus.open
        return result

    # 获取请求目标交易盘易持仓
    def __get_sp_response(self):
        try:
            t = (dt.datetime.now() - self._last_order_time).seconds
            if t < 5:
                time.sleep(5 - t)
        except:
            pass
        r = None
        e1 = None
        # 尝试重复三次获取，防止偶然性网络错误
        for i in range(3):
            try:
                r = self._client.get_positions(self._client_param)
                break
            except Exception as e:
                e1 = e
                # 尝试自动登录通达信,防止通达信没有启动
                try:
                    if self._auto_restart_shipane:
                        self._logger.warning('[实盘易] 获取持仓信息错误，尝试自动登录通达信!')
                        self._client.start_clients((5, 60))
                except Exception as E:
                    self._logger.error('[实盘易] 尝试自动登录通达信错误。' + str(E))
                    pass
        if r == None:
            # 重抛异常
            if e1 != None:
                raise e1
        return r

    # 当前时间，用于检测下单是否有效
    @property
    def current_dt(self):
        return dt.datetime.now()

    # 获取一只股票的价格信息,未实现。可考虑从新浪实时行情获取,或直接从聚宽获取。因同步暂时未用到，所以还没写。
    def get_data(self, stock):
        return TraderSecurityUnitData(price=None, high_limit=None)


'''------------------------EasyTrader交易盘 未完成----------------------'''
try:
    import easytrader
except:
    pass


class YH_EasyTrader(TraderBase):
    def __init__(self, logger, **kwargs):
        TraderBase.__init__(self)
        self._logger = logger
        self._client = easytrader.use('yh', debug=kwargs.get('debug', False))
        self.user = kwargs.get('user', '')
        self.password = kwargs.get('password', '')
        self._client.prepare(user=self.user, password=self.password)

    def login(self):
        self._client.prepare(user=self.user, password=self.password)

    @property
    def portfolio(self):
        pf = TraderPortfolio()

        b = self._client.balance[0]
        pf.available_cash = b[u'可用资金']
        pf.positions_value = b[u'参考市值']
        ps = self._client.position
        for p in ps:
            stock = p[u'证券代码'].encode('utf-8')
            pf.positions[stock] = TraderPosition(security=stock
                                                 , total_amount=int(p[u'当前持仓'])
                                                 , closeable_amount=int(p[u'股份余额'])
                                                 , price=float(p[u'参考市价'])
                                                 , avg_cost=float(p[u'参考成本价']))
        return pf

    # 下单，规整为统一类型的下单返回未实现
    def order(self, **kwargs):
        self._last_order_time = dt.datetime.now()

        if kwargs.get('action', '') == 'SELL':
            self._client.sell(kwargs.get('symbol', ''), entrust_prop='market', amount=kwargs.get('amount', 0))
        else:
            self._client.buy(kwargs.get('symbol', ''), entrust_prop='market', amount=kwargs.get('amount', 0))

    # 获取请求目标交易盘易持仓
    def __get_sp_response(self):
        try:
            t = (dt.datetime.now() - self._last_order_time).seconds
            if t < 5:
                time.sleep(5 - t)
        except:
            pass
        r = None
        e1 = None
        # 尝试重复三次获取，防止偶然性网络错误
        for i in range(3):
            try:
                r = self._client.get_positions(self._client_param)
                break
            except Exception as e:
                e1 = e
                # 尝试自动登录通达信,防止通达信没有启动
                try:
                    if self._auto_restart_shipane:
                        self._logger.warning('[EasyTrader] 获取持仓信息错误，尝试自动登录通达信!')
                        self._client.start_clients((5, 60))
                except Exception as E:
                    self._logger.error('[EasyTrader] 尝试自动登录通达信错误。' + str(E))
                    pass
        if r == None:
            # 重抛异常
            if e1 != None:
                raise e1
        return r

    # 当前时间，用于检测下单是否有效
    @property
    def current_dt(self):
        return dt.datetime.now()

    # 获取一只股票的价格信息,未实现。可考虑从新浪实时行情获取,或直接从聚宽获取。因同步暂时未用到，所以还没写。
    def get_data(self, stock):
        return TraderSecurityUnitData(price=None, high_limit=None)


'''---------------------------聚宽  交易盘类--------------------'''
try:
    from kuanke.user_space_api import *
except:
    pass


# ''' 聚宽 交易盘 '''
class JoinQuantTrader(TraderBase):
    def __init__(self, **kwargs):
        TraderBase.__init__(self)

    @property
    def portfolio(self):
        # 因TraderPortfolio和TraderPosition是以聚宽的定义为模板定义的
        # 聚宽portfolio包含了所有TraderPortfolio的定义，所以直接返回外部就能调用
        return self.context.portfolio

    # 下单，规整为统一类型的下单返回未实现
    def order(self, **kwargs):
        security = kwargs.get('symbol', None)
        amount = kwargs.get('amount', 0)
        is_buy = kwargs.get('action', 'BUY') == 'BUY'
        if not is_buy:
            amount = -amount
        return order(security, amount)

    # 当前时间，用于检测下单是否有效
    @property
    def current_dt(self):
        return self.context.current_dt

    # 获取一只股票的价格信息
    def get_data(self, stock):
        if self.data != None:
            return TraderSecurityUnitData(price=self.data[stock].close, high_limit=self.data[stock].high_limit)
        else:
            price = attribute_history(stock, 1, '1m', ('close'), True)['close'][0]
            high_limit = get_current_data()[stock].high_limit
            return TraderSecurityUnitData(price=price, high_limit=high_limit)


# ''' 米筐 交易盘 未完成'''
class RichQuantTrader(TraderBase):
    def __init__(self, **kwargs):
        TraderBase.__init__(self)

    @property
    def portfolio(self):
        pf = TraderPortfolio()
        pf.available_cash = self.context.portfolio.cash
        pf.available_cash = self.context.portfolio.market_value

        for rich_p in self.context.portfolio.positions.values():
            tp = TraderPosition(security=rich_p.order_book_id  # 股票代码
                                , price=rich_p.market_value / rich_p.quantity  # 当前股价
                                , avg_cost=rich_p.avg_price  # 平均成本
                                , total_amount=rich_p.quantity  # 当前持仓数
                                , closeable_amount=rich_p.sellable  # 可卖数量
                                )
            pf.positions[rich_p.order_book_id] = tp
        return pf

    # 下单，规整为统一类型的下单返回未实现
    def order(self, **kwargs):
        security = kwargs.get('symbol', None)
        amount = kwargs.get('amount', 0)
        is_buy = kwargs.get('action', 'BUY') == 'BUY'
        if not is_buy:
            amount = -amount
        return order_shares(security, amount)

    # 当前时间，用于检测下单是否有效
    @property
    def current_dt(self):
        return self.context.now

    # 获取一只股票的价格信息
    def get_data(self, stock):
        if self.data != None:
            return TraderSecurityUnitData(price=self.data[stock].close, high_limit=self.data[stock].limit_up)
        else:
            rich_price = get_price(stock, self.context.now, end_date=None, frequency='1m', fields=None,
                                   adjust_type='pre', skip_suspended=False)
            price = rich_price['close'][-1]
            high_limit = rich_price['limit_up'][-1]
            return TraderSecurityUnitData(price=price, high_limit=high_limit)

    def login(self):
        pass


# '''-------------[聚宽模拟盘持仓] 同步到 [实盘易 持仓] 的调用类-----------------------'''
class JoinQuantSyncPosition(object):
    def __init__(self, **kwargs):
        try:
            log
            self._logger = shipane_sdk._Logger()
        except NameError:
            import logging
            self._logger = logging.getLogger()
        joinquant_trader = JoinQuantTrader()
        shipane_trader = ShipaneTrader(self._logger, **kwargs)
        self.syncer = TraderSynchronizer(self._logger
                                         , joinquant_trader
                                         , shipane_trader
                                         , normalize_code=normalize_code  # 替换规整股票代码的函数为聚宽的函数
                                         , **kwargs)

    # 执行同步
    def execute(self, context, data):
        return self.syncer.execute(context, data)

    # 获取源交易盘总资产-目标交易盘总资产的资金差额
    def difference_cash(self, context, data):
        return self.syncer.difference_cash(context, data)


# '''------------- [实盘易 持仓] 同步到 [聚宽模拟盘持仓]  的调用类-----------------------'''
class Shipane_Sync_to_JoinQuant(object):
    def __init__(self, **kwargs):
        try:
            log
            self._logger = shipane_sdk._Logger()
        except NameError:
            import logging
            self._logger = logging.getLogger()
        joinquant_trader = JoinQuantTrader()
        shipane_trader = ShipaneTrader(self._logger, **kwargs)
        self.syncer = TraderSynchronizer(self._logger
                                         , shipane_trader
                                         , joinquant_trader
                                         , normalize_code=normalize_code  # 替换规整股票代码的函数为聚宽的函数
                                         , **kwargs)

    # 执行同步
    def execute(self, context, data):
        return self.syncer.execute(context, data)

    # 获取源交易盘总资产-目标交易盘总资产的资金差额
    def difference_cash(self, context, data):
        return self.syncer.difference_cash(context, data)
