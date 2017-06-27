# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.db import transaction
from decimal import Decimal
from wallet.forms import WalletUpdateBalanceModelForm

from orders.models import PayOrders, PAY_ORDERS_TYPE
from users.models import ConsumerUser

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
        return self.user_id

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
    def update_balance(cls, orders_id=None, user_id=None, amount_of_money=None, method=None):
        kwargs = {'user_id': user_id,
                  'orders_id': orders_id,
                  'amount_of_money': amount_of_money,
                  'method': method}
        form = WalletUpdateBalanceModelForm(kwargs)
        if not form.is_valid():
            return form.errors

        verify_result = WalletActionBase().verify_action_params(
            orders_id=orders_id,
            user_id=user_id,
            amount_of_money=amount_of_money,
            method=method,
        )
        if verify_result is not True:
            return verify_result

        _user = cls.get_object(**{'user_id': user_id})
        # 如果当前用户没有钱包，则创建钱包
        if isinstance(_user, Exception):
            cls.create_wallet(user_id)
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
    trade_status = models.IntegerField('订单支付状态', default=0)
    # 交易类型 0: 未指定 1: 充值 2：消费 3: 取现
    trade_type = models.IntegerField('订单类型', default=0)
    # 金额是否同步到了钱包 0: 未同步 1: 已同步
    is_sync = models.IntegerField('金额是否同步', default=0)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = WalletManager()

    class Meta:
        db_table = 'ys_wallet_trade_detail'
        ordering = ['-updated']

    def __unicode__(self):
        return self.user_id

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
    def get_orders_instance(self, orders_id):
        kwargs = {'orders_id': orders_id}
        return PayOrders.get_success_orders(**kwargs)

    def get_user(self, user_id):
        return ConsumerUser.get_object(**{'pk': user_id})

    def get_wallet_trade_detail(self, orders_id):
        return WalletTradeDetail.get_object(**{'orders_id': orders_id})

    def verify_action_params(self, orders_id=None, user_id=None,
                             amount_of_money=None, method=None):
        _orders = self.get_orders_instance(orders_id)
        if isinstance(_orders, Exception):
            return _orders
        _user = self.get_user(user_id)
        if isinstance(_user, Exception):
            return _user
        _wallet_detail = self.get_wallet_trade_detail(orders_id)
        if isinstance(_wallet_detail, Exception):
            return _wallet_detail
        if _wallet_detail.user_id != user_id:
            return ValueError('The user ID and orders ID do not match')
        if _wallet_detail.is_sync:
            return ValueError('Already recharged')
        if amount_of_money != _orders.payable:
            return ValueError('Amount of money is incorrect')
        if _orders.orders_type != PAY_ORDERS_TYPE['wallet_%s' % method]:
            return ValueError('Cannot perform this action')

        return True


class WalletAction(object):
    """
    钱包相关功能
    """
    def recharge(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        充值
        """
        # 去充值
        result = Wallet.update_balance(user_id=user_id,
                                       orders_id=orders_id,
                                       amount_of_money=amount_of_money,
                                       method='recharge')
        return result

    def consume(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        消费
        """

    def withdrawals(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        提现
        """
