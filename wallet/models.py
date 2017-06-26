# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from horizon.models import model_to_dict
from horizon.main import minutes_30_plus, DatetimeEncode
from django.db import transaction
from decimal import Decimal

from Business_App.bz_dishes.models import Dishes
from Business_App.bz_orders.models import OrdersIdGenerator

import json
import datetime


class OrdersManager(models.Manager):
    def get(self, *args, **kwargs):
        object_data = super(OrdersManager, self).get(*args, **kwargs)
        if now() >= object_data.expires and object_data.payment_status == 0:
            object_data.payment_status = 400
        return object_data

    def filter(self, *args, **kwargs):
        object_data = super(OrdersManager, self).filter(*args, **kwargs)
        for item in object_data:
            if now() >= item.expires and item.payment_status == 0:
                item.payment_status = 400
        return object_data


class Wallet(models.Model):
    """
    用户钱包
    """
    user_id = models.IntegerField('用户ID', db_index=True)
    balance = models.CharField('余额', max_length=16, default='0')
    password = models.CharField('支付密码', max_length=560)
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
        except Wallet.DoesNotExist:
            return cls()

    @classmethod
    def update_payment_status_by_pay_callback(cls, orders_id, validated_data):
        if not isinstance(validated_data, dict):
            raise ValueError('Parameter error')

        payment_status = validated_data.get('payment_status')
        payment_mode = validated_data.get('payment_mode')
        if payment_status not in (200, 400, 500):
            raise ValueError('Payment status must in range [200, 400, 500]')
        if payment_mode not in [1, 2, 3]:    # 钱包支付、微信支付和支付宝支付
            raise ValueError('Payment mode must in range [1, 2, 3]')
        instance = None
        # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(orders_id=orders_id)
            except cls.DoesNotExist:
                raise cls.DoesNotExist
            if _instance.payment_status != 0:
                raise Exception('Cannot perform this action')
            _instance.payment_status = payment_status
            _instance.payment_mode = payment_mode
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

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    extend = models.TextField('扩展信息', default='', blank=True)

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
