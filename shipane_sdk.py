# coding=utf-8

import copy
import datetime
import re
import lxml.html
import pandas as pd
import requests
import six
from lxml import etree
from pandas.compat import StringIO
from requests import Request
from six.moves.urllib.parse import urlencode


class Client(object):
    KEY_REGEX = r'key=([^&]*)'

    def __init__(self, logger=None, **kwargs):
        if logger is not None:
            self._logger = logger
        else:
            import logging
            self._logger = logging.getLogger(__name__)
        self._host = kwargs.pop('host', 'localhost')
        self._port = kwargs.pop('port', 8888)
        self._key = kwargs.pop('key', '')
        self._timeout = kwargs.pop('timeout', (10.0, 30.0))
        self._log_level = kwargs.pop('log_level', ['info', 'debug', 'waring', 'error'])

    @property
    def log_level(self):
        try:
            return self._log_level
        except:
            return ['info', 'debug', 'waring', 'error']

    @log_level.setter
    def log_level(self, value):
        self._log_level = value

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    def get_account(self, client=None, timeout=None):
        request = Request('GET', self.__create_url(client, 'accounts'))
        response = self.__send_request(request, timeout)
        return response.json()

    def get_orders(self, client=None, timeout=None):
        request = Request('GET', self.__create_url(client, 'orders'))
        response = self.__send_request(request, timeout)
        json = response.json()
        count = json['count']
        orders = pd.DataFrame(json['dataTable']['rows'], columns=json['dataTable']['columns'])
        return {'count': count, 'orders': orders}

    def get_positions(self, client=None, timeout=None):
        request = Request('GET', self.__create_url(client, 'positions'))
        response = self.__send_request(request, timeout)
        json = response.json()
        sub_accounts = pd.DataFrame(json['subAccounts']).T
        positions = pd.DataFrame(json['dataTable']['rows'], columns=json['dataTable']['columns'])
        return {'sub_accounts': sub_accounts, 'positions': positions}

    def buy(self, client=None, timeout=None, **kwargs):
        kwargs['action'] = 'BUY'
        return self.__execute(client, timeout, **kwargs)

    def sell(self, client=None, timeout=None, **kwargs):
        kwargs['action'] = 'SELL'
        return self.__execute(client, timeout, **kwargs)

    def execute(self, client=None, timeout=None, **kwargs):
        return self.__execute(client, timeout, **kwargs)

    def cancel(self, client=None, order_id=None, timeout=None):
        request = Request('DELETE', self.__create_order_url(client, order_id))
        self.__send_request(request, timeout)

    def cancel_all(self, client=None, timeout=None):
        request = Request('DELETE', self.__create_order_url(client))
        self.__send_request(request, timeout)

    def query(self, client=None, navigation=None, timeout=None):
        request = Request('GET', self.__create_url(client, '', navigation=navigation))
        response = self.__send_request(request, timeout)
        json = response.json()
        df = pd.DataFrame(json['dataTable']['rows'], columns=json['dataTable']['columns'])
        return df

    def query_new_stocks(self):
        return self.__query_new_stocks()

    def purchase_new_stocks(self, client=None, timeout=None):
        today = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
        df = self.query_new_stocks()
        df = df[(df.ipo_date == today)]
        if 'info' in self.log_level:
            self._logger.info('今日可申购新股有[%d]只', len(df))
        for index, row in df.iterrows():
            try:
                order = {
                    'symbol': row['xcode'], 'type': 'LIMIT', 'price': row['price'], 'amountProportion': 'ALL'
                }
                if 'info' in self.log_level:
                    self._logger.info('申购新股：%s', str(order))
                self.buy(client, timeout, **order)
            except Exception as e:
                if 'error' in self.log_level:
                    self._logger.error('客户端[%s]申购新股[%s(%s)]失败\n%s', client, row['name'], row['code'], e)

    def start_clients(self, timeout=None):
        request = Request('PUT', self.__create_url(None, 'clients'))
        self.__send_request(request, timeout)

    def shutdown_clients(self, timeout=None):
        request = Request('DELETE', self.__create_url(None, 'clients'))
        self.__send_request(request, timeout)

    def __execute(self, client=None, timeout=None, **kwargs):
        if not kwargs.get('type'):
            kwargs['type'] = 'LIMIT'
        request = Request('POST', self.__create_order_url(client), json=kwargs)
        response = self.__send_request(request)
        return response.json()

    def __query_new_stocks(self):
        DATA_URL = 'http://vip.stock.finance.sina.com.cn/corp/view/vRPD_NewStockIssue.php?page=1&cngem=0&orderBy=NetDate&orderType=desc'
        html = lxml.html.parse(DATA_URL)
        res = html.xpath('//table[@id=\"NewStockTable\"]/tr')
        if six.PY2:
            sarr = [etree.tostring(node) for node in res]
        else:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        sarr = ''.join(sarr)
        sarr = sarr.replace('<font color="red">*</font>', '')
        sarr = '<table>%s</table>' % sarr
        df = pd.read_html(StringIO(sarr), skiprows=[0, 1])[0]
        df = df.select(lambda x: x in [0, 1, 2, 3, 7], axis=1)
        df.columns = ['code', 'xcode', 'name', 'ipo_date', 'price']
        df['code'] = df['code'].map(lambda x: str(x).zfill(6))
        df['xcode'] = df['xcode'].map(lambda x: str(x).zfill(6))
        return df

    def __create_order_url(self, client=None, order_id=None, **params):
        return self.__create_url(client, 'orders', order_id, **params)

    def __create_url(self, client, resource, resource_id=None, **params):
        all_params = copy.deepcopy(params)
        if client is not None:
            all_params.update(client=client)
        all_params.update(key=self._key)
        if resource_id is None:
            path = '/{}'.format(resource)
        else:
            path = '/{}/{}'.format(resource, resource_id)

        return '{}{}?{}'.format(self.__create_base_url(), path, urlencode(all_params))

    def __create_base_url(self):
        return 'http://' + self._host + ':' + str(self._port)

    def __send_request(self, request, timeout=None):
        prepared_request = request.prepare()
        timeout = timeout if timeout is not None else self._timeout
        self.__log_request(prepared_request)
        with requests.sessions.Session() as session:
            response = session.send(prepared_request, timeout=timeout)
        self.__log_response(response)
        response.raise_for_status()
        return response

    def __log_request(self, prepared_request):
        url = self.__eliminate_privacy(prepared_request.path_url)
        if prepared_request.body is None:
            if 'info' in self.log_level:
                self._logger.info('Request:\n%s %s', prepared_request.method, url)
        else:
            if 'info' in self.log_level:
                self._logger.info('Request:\n%s %s\n%s', prepared_request.method, url, prepared_request.body)

    def __log_response(self, response):
        message = 'Response:\n{} {}\n{}'.format(response.status_code, response.reason, response.text)
        if response.status_code == 200:
            if 'info' in self.log_level:
                self._logger.info(message)
        else:
            if 'error' in self.log_level:
                self._logger.error(message)

    @classmethod
    def __eliminate_privacy(cls, url):
        match = re.search(cls.KEY_REGEX, url)
        key = match.group(1)
        masked_key = '*' * len(key)
        url = re.sub(cls.KEY_REGEX, "key={}".format(masked_key), url)
        return url


# -*- coding: utf-8 -*-

import datetime
try:
    from kuanke.user_space_api import *
except:
    pass

class JoinQuantExecutor(object):
    def __init__(self, **kwargs):
        try:
            log
            self._logger = _Logger()
        except NameError:
            import logging
            self._logger = logging.getLogger()
        self._client = shipane_sdk.Client(self._logger, **kwargs)
        self._client_param = kwargs.get('client')
        self._order_id_map = dict()
        self._expire_before = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

    @property
    def client(self):
        return self._client

    def purchase_new_stocks(self):
        self.client.purchase_new_stocks(self._client_param)

    def execute(self, order):
        self._logger.info("[实盘易] 跟单：" + str(order))

        if order is None:
            self._logger.info('[实盘易] 委托为空，忽略下单请求')
            return
        if self.__is_expired(order):
            self._logger.info('[实盘易] 委托已过期，忽略下单请求')
            return

        try:
            action = 'BUY' if order.is_buy else 'SELL'
            order_type = 'LIMIT' if order.limit > 0 else 'MARKET'
            price_type = 0 if order_type == 'LIMIT' else 4
            actual_order = self._client.execute(self._client_param,
                                                action=action,
                                                symbol=order.security,
                                                type=order_type,
                                                priceType=price_type,
                                                price=order.limit,
                                                amount=order.amount)
            self._order_id_map[order.order_id] = actual_order['id']
            return actual_order
        except Exception as e:
            self._logger.error("[实盘易] 下单异常：" + str(e))

    def cancel(self, order):
        if order is None:
            self._logger.info('[实盘易] 委托为空，忽略撤单请求')
            return

        try:
            order_id = order if isinstance(order, int) else order.order_id
            if order_id in self._order_id_map:
                self._client.cancel(self._client_param, self._order_id_map[order_id])
            else:
                self._logger.warning('[实盘易] 未找到对应的委托编号')
        except Exception as e:
            self._logger.error("[实盘易] 撤单异常：" + str(e))

    def __is_expired(self, order):
        return order.add_time < self._expire_before


class _Logger(object):
    def debug(self, msg, *args, **kwargs):
        log.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        log.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        log.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        log.error(msg, *args, **kwargs)
