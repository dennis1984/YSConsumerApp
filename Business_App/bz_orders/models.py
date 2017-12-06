# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.timezone import now
from django.db import transaction

from horizon.main import minutes_15_plus
from horizon.models import model_to_dict, get_perfect_filter_params
from coupons.models import Coupons
from Business_App.bz_dishes.models import DISHES_MARK_DISCOUNT_VALUES
from Admin_App.ad_coupons.models import DishesDiscountConfig
from Business_App.bz_wallet.models import WalletAction

import json
from decimal import Decimal


ORDERS_PAYMENT_STATUS = {
    'unpaid': 0,
    'paid': 200,
    'consuming': 201,
    'finished': 206,
    'expired': 400,
    'failed': 500,
}

ORDERS_ORDERS_TYPE = {
    'unknown': 0,
    'online': 101,
    'business': 102,
    'take_out': 103,
    'wallet_recharge': 201,
    'wallet_withdraw': 203,
}


class Orders(models.Model):
    """
    订单数据模型
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=30)
    user_id = models.IntegerField('用户ID', db_index=True)
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)
    business_name = models.CharField('商户名字', max_length=100)

    dishes_ids = models.TextField('订购列表', default='')
    # 订购列表详情
    # [
    #  {'id': 1, ...},   # 菜品详情
    #  {'id': 2, ...}, ...
    # ]
    #
    total_amount = models.CharField('订单总计', max_length=16, default='0')
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    online_discount = models.CharField('在线下单优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    coupons_discount = models.CharField('优惠券优惠', max_length=16, default='0')
    service_dishes_subsidy = models.CharField('菜品优惠平台补贴', max_length=16, default='0')
    service_coupons_subsidy = models.CharField('优惠券优惠平台补贴', max_length=16, default='0')
    payable = models.CharField('订单总计', max_length=16, default='0')

    coupons_id = models.IntegerField('优惠券ID', null=True)

    # 0:未支付 200:已支付 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=0)
    # 支付方式：0:未指定支付方式 1：现金支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    orders_type = models.IntegerField('订单类型', default=102)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_orders'
        ordering = ['-orders_id']
        app_label = 'Business_App.bz_orders.models.Orders'

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e


def date_for_model():
    return now().date()


def ordersIdIntegerToString(orders_id):
    return "%06d" % orders_id


class OrdersIdGenerator(models.Model):
    """
    订单号生成器
    """
    date = models.DateField('日期', primary_key=True, default=date_for_model)
    orders_id = models.IntegerField('订单ID', default=1)
    created = models.DateTimeField('创建日期', default=now)
    updated = models.DateTimeField('最后更改日期', auto_now=True)

    class Meta:
        db_table = 'ys_orders_id_generator'
        app_label = 'Business_App.bz_orders.models.OrdersIdGenerator'

    def __unicode__(self):
        return str(self.date)

    @classmethod
    def get_orders_id(cls):
        date_day = date_for_model()
        # 数据库加排它锁，保证订单号是唯一的
        with transaction.atomic(using='business'):   # 多数据库事务管理需显示声明操作的数据库
                                                     # （以后的版本可能会改进）
            try:
                _instance = cls.objects.select_for_update().get(pk=date_day)
            except cls.DoesNotExist:
                cls().save()
                orders_id = 1
            else:
                orders_id = _instance.orders_id + 1
                _instance.orders_id = orders_id
                _instance.save()
        orders_id_string = ordersIdIntegerToString(orders_id)
        return '%s%s' % (date_day.strftime('%Y%m%d'), orders_id_string)


class VerifyOrders(models.Model):
    """
    核销订单模型
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    business_name = models.CharField('商户名字', max_length=200)
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)
    consumer_id = models.IntegerField('消费者ID')

    dishes_ids = models.TextField('订购列表', default='')

    total_amount = models.CharField('订单总计', max_length=16)
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    online_discount = models.CharField('在线下单优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    coupons_discount = models.CharField('优惠券优惠', max_length=16, default='0')
    service_dishes_subsidy = models.CharField('菜品优惠平台补贴', max_length=16, default='0')
    service_coupons_subsidy = models.CharField('优惠券优惠平台补贴', max_length=16, default='0')
    payable = models.CharField('应付金额', max_length=16)

    coupons_id = models.IntegerField('优惠券ID', null=True)

    # 0:未支付 200:已支付 201:待消费 206:已完成 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=201)
    # 支付方式：0:未指定支付方式 1：钱包支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    orders_type = models.IntegerField('订单类型', default=101)

    notes = models.CharField('订单备注', max_length=40, default='')
    # 核销时段：例如：17:30~20:30
    consumer_time_slot = models.CharField('订单核销时间段', max_length=32, null=True, blank=True)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    # objects = OrdersManager()

    class Meta:
        db_table = 'ys_verify_orders'
        app_label = 'Business_App.bz_orders.models.VerifyOrders'

    def __unicode__(self):
        return self.orders_id

    @property
    def is_success(self):
        """
        订单是否完成
        """
        if self.payment_status == ORDERS_PAYMENT_STATUS['finished']:
            return True
        return False

    @property
    def is_consume_orders(self):
        """
        消费订单
        """
        if self.orders_type not in (ORDERS_ORDERS_TYPE['wallet_withdraw'],
                                    ORDERS_ORDERS_TYPE['unknown']):
            return True
        return False


class VerifyOrdersAction(object):
    """
    核销订单
    """
    def is_ys_pay_orders(self, consume_orders):
        kwargs = {'consume_orders_id': consume_orders.orders_id}
        instance = YinshiPayCode.get_object(**kwargs)
        if isinstance(instance, Exception):
            return False
        return True

    def is_valid_consume_orders(self, consume_orders):
        error_message = 'Orders data is incorrect.'
        if consume_orders.orders_type != ORDERS_ORDERS_TYPE['online']:
            return False, Exception(error_message)
        if self.is_ys_pay_orders(consume_orders):
            if consume_orders.payment_status != ORDERS_PAYMENT_STATUS['finished']:
                return False, Exception(error_message)
        else:
            if consume_orders.payment_status != ORDERS_PAYMENT_STATUS['consuming']:
                return False, Exception(error_message)
        return True, None

    def create(self, consume_orders, pay_orders):
        """
        创建核销订单
        return: None: 成功
                Exception：失败
        """
        is_valid, result = self.is_valid_consume_orders(consume_orders)
        if not is_valid:
            return result

        service_dishes_subsidy = '0'
        service_coupons_subsidy = '0'

        # 优惠券平台补贴计算
        dishes_detail_list = json.loads(pay_orders.dishes_ids)
        business_count = float(len(dishes_detail_list))
        if consume_orders.coupons_id:
            coupons_detail = Coupons.get_perfect_detail(pk=consume_orders.coupons_id,
                                                        user_id=consume_orders.user_id)
            if isinstance(coupons_detail, Exception):
                return coupons_detail

            amount_of_money = float(coupons_detail['amount_of_money'])
            service_ratio = coupons_detail['service_ratio'] / 100.0
            verify_discount = '%.2f' % ((amount_of_money / business_count) * service_ratio)
            service_coupons_subsidy = verify_discount

        # 菜品折扣平台补贴计算
        dishes_detail_list = json.loads(consume_orders.dishes_ids)
        for index, dishes_detail in enumerate(dishes_detail_list, 1):
            if dishes_detail['mark'] in DISHES_MARK_DISCOUNT_VALUES and \
                            pay_orders.orders_type == ORDERS_ORDERS_TYPE['online']:

                dishes_discount_config = DishesDiscountConfig.get_object(dishes_id=dishes_detail['id'])
                if isinstance(dishes_discount_config, Exception):
                    continue
                service_ratio = dishes_discount_config.service_ratio / 100.0
                dishes_subsidy = '%.2f' % float(str(Decimal(dishes_detail['discount']) *
                                                    dishes_detail['count'] *
                                                    Decimal(service_ratio)))
                service_dishes_subsidy = str(Decimal(service_dishes_subsidy) +
                                             Decimal(dishes_subsidy))

        update_data = {'user_id': consume_orders.business_id,
                       'consumer_id': consume_orders.user_id,
                       'service_dishes_subsidy': service_dishes_subsidy,
                       'service_coupons_subsidy': service_coupons_subsidy,
                       'payable': str(Decimal(consume_orders.payable) +
                                      Decimal(service_dishes_subsidy) +
                                      Decimal(service_coupons_subsidy))}
        orders_data = model_to_dict(consume_orders)
        pop_keys = ['created', 'updated', 'master_orders_id',
                    'is_commented', 'confirm_code', 'business_id',
                    'stalls_number']
        for key in pop_keys:
            orders_data.pop(key)

        orders_data.update(update_data)
        try:
            obj = VerifyOrders(**orders_data)
            obj.save()
        except Exception as e:
            return e

        if obj.is_success:
            # 更新商户端钱包余额
            result = WalletAction().income(obj)
            if isinstance(result, Exception):
                return result
            # 把商户对应的订单隐藏掉（置为过期状态）（商户端选择吟食支付时，用户端会重新下单并支付，
                # 最后再把核销订单同步到商户端，所以商户端的最原始订单已经无效了）
            yspay_ins = YinshiPayCode.get_object(consume_orders_id=obj.orders_id)
            if not isinstance(yspay_ins, Exception):
                orders_ins = Orders.get_object(orders_id=yspay_ins.business_orders_id)
                orders_ins.expires = now()
                orders_ins.save()

        return obj


class YSPayManager(models.Manager):
    def get(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(YSPayManager, self).get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        kwargs['expires__gt'] = now()
        return super(YSPayManager, self).filter(*args, **kwargs)


class YinshiPayCode(models.Model):
    """
    吟食支付随机码
    """
    user_id = models.IntegerField('用户ID')
    dishes_ids = models.TextField('订购商品列表')
    business_orders_id = models.CharField('商户端对应的订单ID', max_length=32)
    pay_orders_id = models.CharField('支付订单ID', max_length=32,
                                     blank=True, null=True, default='')
    consume_orders_id = models.CharField('核销订单ID', max_length=32,
                                         blank=True, null=True, default='')
    code = models.CharField('随机码', max_length=32, db_index=True)
    expires = models.DateTimeField('过期时间', default=minutes_15_plus)
    created = models.DateTimeField('创建日期', default=now)

    objects = YSPayManager()

    class Meta:
        db_table = 'ys_yinshi_pay_code'
        app_label = 'Business_App.bz_orders.models.YinshiPayCode'

    def __unicode__(self):
        return str(self.code)

    @classmethod
    def get_object(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

