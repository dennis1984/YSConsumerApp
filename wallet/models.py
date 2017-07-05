# -*- coding:utf8 -*-
from __future__ import unicode_literals
from rest_framework.request import Request
from django.http.request import HttpRequest

from django.db import models
from django.utils.timezone import now
from django.db import transaction
from decimal import Decimal

from orders.models import (PayOrders,
                           TradeRecordAction,
                           ORDERS_ORDERS_TYPE)
from horizon.models import model_to_dict

import json
import datetime


WALLET_TRADE_DETAIL_TRADE_TYPE_DICT = {
    'recharge': 1,
    'consume': 2,
    'withdrawals': 3,
}

WALLET_ACTION_METHOD = ('recharge', 'consume', 'withdrawals')


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
    password = models.CharField('支付密码', max_length=560, null=True)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_wallet'

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def has_enough_balance(cls, request, amount_of_money):
        wallet = cls.get_object(**{'user_id': request.user.id})
        if isinstance(wallet, Exception):
            return False
        try:
            return Decimal(wallet.balance) >= Decimal(amount_of_money)
        except:
            return False

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
    def update_balance(cls, request, orders, method):
        verify_result = WalletActionBase().verify_action_params(
            orders=orders,
            request=request,
            method=method,
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

        # 判断当前余额是否够用
        if method != WALLET_ACTION_METHOD[0]:
            if Decimal(_wallet.balance) < Decimal(amount_of_money):
                return ValueError('Balance is not enough')

        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(user_id=user_id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist
            balance = _instance.balance
            # 充值
            if method == WALLET_ACTION_METHOD[0]:
                _instance.balance = str(Decimal(balance) + Decimal(amount_of_money))
            else:
                _instance.balance = str(Decimal(balance) - Decimal(amount_of_money))
            _instance.save()
            instance = _instance
        return instance


class WalletTradeDetail(models.Model):
    """
    交易明细
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    amount_of_money = models.CharField('金额', max_length=16)

    # 交易状态：0:未完成 200:已完成 500:交易失败
    trade_status = models.IntegerField('订单支付状态', default=200)
    # 交易类型 0: 未指定 1: 充值 2：消费 3: 取现
    trade_type = models.IntegerField('订单类型', default=0)
    # 金额是否同步到了钱包 0: 未同步 1: 已同步
    is_sync = models.IntegerField('金额是否同步', default=1)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = WalletManager()

    class Meta:
        db_table = 'ys_wallet_trade_detail'
        ordering = ['-updated']

    def __unicode__(self):
        return str(self.user_id)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_success_list(cls, **kwargs):
        kwargs['trade_status'] = 200
        try:
            return cls.objects.filter(**kwargs)
        except:
            return []


class WalletActionBase(object):
    """
    钱包相关功能
    """
    def get_wallet_trade_detail(self, orders_id):
        return WalletTradeDetail.get_object(**{'orders_id': orders_id})

    def verify_action_params(self, request, orders, method=None):
        if not isinstance(orders, PayOrders):
            return TypeError('Params orders must be PayOrders instance')

        wallet_detail = self.get_wallet_trade_detail(orders.orders_id)
        if not isinstance(wallet_detail, Exception):
            return TypeError('Cannot perform this action')
        if orders.user_id != request.user.id:
            return ValueError('The user ID and orders ID do not match')

        if method == WALLET_ACTION_METHOD[0]:  # 充值操作
            if not orders.is_success:
                return ValueError('Orders Data is Error')
            if not orders.is_recharge_orders:
                return ValueError('Orders Type is Error')
        else:
            if not orders.is_payable:
                return ValueError('Orders status is incorrect')
            if orders.has_payment_mode:
                return ValueError('Orders status is incorrect')

        if ('wallet_%s' % method) in ORDERS_ORDERS_TYPE:
            if orders.orders_type != ORDERS_ORDERS_TYPE['wallet_%s' % method]:
                return ValueError('Cannot perform this action')
        else:
            if orders.orders_type not in ORDERS_ORDERS_TYPE.values():
                return ValueError('Orders Type is incorrect')

        return True


class WalletAction(object):
    """
    钱包相关功能
    """
    def has_enough_balance(self, request, orders):
        if not isinstance(orders, PayOrders):
            return False
        return Wallet.has_enough_balance(request, orders.payable)

    def recharge(self, request, orders, gateway='auth'):
        """
        充值
        """
        if gateway == 'pay_callback':
            request = Request(HttpRequest)
            try:
                setattr(request.user, 'id', orders.user_id)
            except Exception as e:
                return e
        # 去充值
        result = Wallet.update_balance(request=request,
                                       orders=orders,
                                       method=WALLET_ACTION_METHOD[0])
        # 生成消费记录
        _trade = WalletTradeAction().create(request, orders)
        if isinstance(_trade, Exception):
            return _trade
        return result

    def consume(self, request, orders):
        """
        消费
        """
        if not self.has_enough_balance(request, orders):
            return ValueError('Balance is not enough')
        _ins = Wallet.update_balance(request=request,
                                     orders=orders,
                                     method=WALLET_ACTION_METHOD[1])
        if isinstance(_ins, Exception):
            return _ins
        # 回写订单状态
        kwargs = {'orders_id': orders.orders_id,
                  'validated_data':
                      {'payment_status': 200,
                       'payment_mode': 1},
                  }
        try:
            orders = PayOrders.update_payment_status_by_pay_callback(**kwargs)
        except Exception as e:
            return e

        # 生成消费记录
        _trade = WalletTradeAction().create(request, orders)
        if isinstance(_trade, Exception):
            return _trade
        # 添加交易记录
        TradeRecordAction().create(request, orders)

        wallet_dict = model_to_dict(_ins)
        wallet_dict.pop('password')
        return wallet_dict

    def withdrawals(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        提现
        """


class WalletTradeAction(object):
    """
    钱包明细相关功能
    """
    def create(self, request, orders):
        """
        创建交易明细（包含：充值、消费和提现（暂不支持）的交易明细）
        """
        if not isinstance(orders, PayOrders):
            return TypeError('Orders data error')
        if orders.orders_type not in ORDERS_ORDERS_TYPE.values():
            return ValueError('Orders data error')
        if not orders.is_success:
            return ValueError('Orders data error')

        if orders.orders_type == 201:  # 交易类型：充值
            trade_type = WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['recharge']
        else:                          # 交易类型：消费
            trade_type = WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['consume']

        kwargs = {'orders_id': orders.orders_id,
                  'user_id': request.user.id,
                  'trade_type': trade_type,
                  'amount_of_money': orders.payable}

        wallet_detail = WalletTradeDetail(**kwargs)
        try:
            wallet_detail.save()
        except Exception as e:
            return e
        return wallet_detail
