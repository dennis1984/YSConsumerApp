# -*- coding:utf8 -*-
from __future__ import unicode_literals
from rest_framework.request import Request
from django.http.request import HttpRequest

from django.db import models
from django.utils.timezone import now
from django.db import transaction
from decimal import Decimal

from horizon.models import model_to_dict
from horizon.main import days_7_plus

from common.models import SerialNumberGenerator

import json
import datetime


WALLET_TRADE_DETAIL_TRADE_TYPE_DICT = {
    'recharge': 1,
    'income': 2,
    'withdraw': 3,
}
WALLET_ACTION_METHOD = ('recharge', 'income', 'withdraw')

WALLET_BALANCE = '500.00'
WALLET_SERVICE_RATE = '0.006'

WITHDRAW_RECORD_STATUS = {
    'unpaid': 0,
    'finished': 200,
    'expired': 400,
    'failed': 500,
}
ORDERS_ORDERS_TYPE = {
    'unknown': 0,
    'online': 101,
    'business': 102,
    'take_out': 103,
    'wallet_recharge': 201,
}


class WalletManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['trade_status'] = 200
        return super(WalletManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['trade_status'] = 200
        return super(WalletManager, self).filter(*args, **kwargs)


class Wallet(models.Model):
    """
    用户钱包
    """
    user_id = models.IntegerField('用户ID', db_index=True)
    balance = models.CharField('余额', max_length=16, default='0')
    blocked_money = models.CharField('冻结金额', max_length=16, default='500.00')
    password = models.CharField('支付密码', max_length=560, null=True)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_wallet'
        app_label = 'Business_App.bz_wallet.models.Wallet'

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def create_wallet(cls, user_id):
        _ins = cls(**{'user_id': user_id})
        _ins.save()
        return _ins

    @classmethod
    def update_balance_for_income(cls, request, orders):
        verify_result = WalletActionBase().verify_action_params_for_income(
            orders=orders,
            request=request,
        )
        if verify_result is not True:
            return verify_result
        user_id = request.user.id
        amount_of_money = orders.payable
        _wallet = cls.get_object(**{'user_id': user_id})

        # 如果当前用户没有钱包，则创建钱包
        if isinstance(_wallet, Exception):
            _wallet = cls.create_wallet(user_id)
        try:
            total_fee = int(amount_of_money.split('.')[0])
        except Exception as e:
            return e
        if total_fee < 0:
            return ValueError('Amount of money Error')

        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(user_id=user_id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist
            balance = _instance.balance
            _instance.balance = str(Decimal(balance) + Decimal(amount_of_money))
            _instance.save()
            instance = _instance
        return instance


class WalletTradeDetail(models.Model):
    """
    交易明细
    """
    serial_number = models.CharField('流水号', unique=True, max_length=32)
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    amount_of_money = models.CharField('金额', max_length=16)

    # 交易状态：0:未完成 200:已完成 500:交易失败
    trade_status = models.IntegerField('订单支付状态', default=200)
    # 交易类型 0: 未指定 1: 充值 2：订单收入 3: 提现
    trade_type = models.IntegerField('订单类型', default=0)

    created = models.DateTimeField('创建时间', default=now)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = WalletManager()

    class Meta:
        db_table = 'ys_wallet_trade_detail'
        ordering = ['-created']
        app_label = 'Business_App.bz_wallet.models.WalletTradeDetail'

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e


class WalletActionBase(object):
    """
    钱包相关功能
    """
    def get_wallet_trade_detail(self, orders_id):
        return WalletTradeDetail.get_object(**{'orders_id': orders_id})

    def verify_action_params_for_income(self, request, orders):
        wallet_detail = self.get_wallet_trade_detail(orders.orders_id)
        if not isinstance(wallet_detail, Exception):
            return TypeError('Cannot perform this action')
        if orders.user_id != request.user.id:
            return ValueError('The user ID and orders ID do not match')

        # 订单收入
        if not orders.is_success:
            return ValueError('Orders Data is Error')
        if not orders.is_consume_orders:
            return ValueError('Orders status is incorrect')
        if orders.orders_type not in ORDERS_ORDERS_TYPE.values():
            return ValueError('Orders Type is incorrect')

        return True


class WalletAction(object):
    """
    钱包相关功能
    """
    def income(self, orders, request=None):
        """
        订单收入
        """
        if not request:
            request = Request(HttpRequest)
            try:
                setattr(request.user, 'id', orders.user_id)
            except Exception as e:
                return e

        # 订单收入
        result = Wallet.update_balance_for_income(request=request,
                                                  orders=orders)
        # 生成交易记录
        _trade = WalletTradeAction().create(request, orders)
        if isinstance(_trade, Exception):
            return _trade
        return result


class WalletTradeAction(object):
    """
    钱包明细相关功能
    """
    def create(self, request, orders, method='income'):
        """
        创建交易明细（包含：充值（暂不支持）、订单收入和提现的交易明细）
        """
        serial_number = SerialNumberGenerator.get_serial_number()
        if method != 'income':
            return Exception('Orders data error')
        if orders.orders_type not in ORDERS_ORDERS_TYPE.values():
            return ValueError('Orders data error')
        if not orders.is_success:
            return ValueError('Orders data error')

        # 交易类型：订单收入
        trade_type = WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['income']
        kwargs = {'orders_id': orders.orders_id,
                  'user_id': request.user.id,
                  'trade_type': trade_type,
                  'amount_of_money': orders.payable,
                  'serial_number': serial_number}

        wallet_detail = WalletTradeDetail(**kwargs)
        try:
            wallet_detail.save()
        except Exception as e:
            return e
        return wallet_detail

