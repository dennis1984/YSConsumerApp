# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.timezone import now
from horizon.models import model_to_dict
from horizon.main import minutes_15_plus, DatetimeEncode
from horizon import main
from django.db import transaction
from decimal import Decimal

from Business_App.bz_dishes.models import Dishes
from Business_App.bz_orders.models import (OrdersIdGenerator,
                                           VerifyOrdersAction)

import json
import datetime

FILTER_IN_ORDERS_TYPE = [101, 102, 103]
FILTER_IN_PAYMENT_STATUS = [200, 400, 500]

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
}

ORDERS_PAYMENT_MODE = {
    'unknown': 0,
    'wallet': 1,
    'wxpay': 2,
    'alipay': 3,
}


class OrdersManager(models.Manager):
    query1 = ~Q(payment_status=ORDERS_PAYMENT_STATUS['finished'],
                orders_type=ORDERS_ORDERS_TYPE['wallet_recharge'])

    def get(self, *args, **kwargs):
        object_data = super(OrdersManager, self).get(
             self.query1, *args, **kwargs
        )
        if now() >= object_data.expires and object_data.payment_status == 0:
            object_data.payment_status = 400
        return object_data

    def filter(self, *args, **kwargs):
        object_data = super(OrdersManager, self).filter(
            self.query1, *args, **kwargs
        )
        for item in object_data:
            if now() >= item.expires and item.payment_status == 0:
                item.payment_status = 400
        return object_data


class PayOrders(models.Model):
    """
    支付订单（主订单）
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)

    dishes_ids = models.TextField('订购列表', default='')
    # 订购列表详情
    # {business_id_1: [订购菜品信息],
    #  business_id_2: [订购菜品信息],
    # }
    #
    total_amount = models.CharField('订单总计', max_length=16)
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payable = models.CharField('应付金额', max_length=16)

    # 0:未支付 200:已支付 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=0)
    # 支付方式：0:未指定支付方式 1：钱包 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    #         201: 钱包充值订单  (预留：202：钱包消费订单 203: 钱包提现)
    orders_type = models.IntegerField('订单类型', default=0)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = OrdersManager()

    class Meta:
        db_table = 'ys_pay_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @property
    def is_expired(self):
        if now() >= self.expires:
            return True
        return False

    @property
    def is_payable(self):
        """
        是否是可支付订单
        """
        if self.is_expired:
            return False
        if self.payment_status == 0:
            return True
        return False

    @property
    def is_wallet_payment_mode(self):
        """
        是否是钱包支付模式
        """
        if self.payment_mode == 1:
            return True
        return False

    @property
    def has_payment_mode(self):
        """
        支付模式是否为：未指定
        """
        if self.payment_mode != 0:
            return True
        return False

    @property
    def is_success(self):
        """
        订单是否完成
        :return: 
        """
        if self.payment_status == 200:
            return True
        return False

    @property
    def is_recharge_orders(self):
        """
        充值订单
        """
        if self.orders_type == ORDERS_ORDERS_TYPE['wallet_recharge']:
            return True
        return False

    @property
    def is_consume_orders(self):
        """
        消费订单
        """
        if self.orders_type != ORDERS_ORDERS_TYPE['wallet_recharge']:
            return True
        return False

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_detail(cls, **kwargs):
        _object = cls.get_object(**kwargs)
        if isinstance(_object, Exception):
            return _object
        detail = model_to_dict(_object)
        detail['dishes_ids'] = json.loads(detail['dishes_ids'])
        detail['is_expired'] = _object.is_expired
        return detail

    @classmethod
    def filter_objects(cls, **kwargs):
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects_detail(cls, **kwargs):
        _objects = cls.filter_objects(**kwargs)
        if isinstance(_objects, Exception):
            return _objects
        results = []
        for item in _objects:
            item_dict = model_to_dict(item)
            item_dict['dishes_ids'] = json.loads(item_dict['dishes_ids'])
            item_dict['is_expired'] = item.is_expired
            item_dict['trade_type'] = 'pay'
            item_dict['business_id'] = None
            item_dict['business_name'] = None
            item_dict['master_orders_id'] = None
            item_dict['is_commented'] = None
            results.append(item_dict)
        return results

    @property
    def orders_detail(self):
        detail = model_to_dict(self)
        detail['dishes_ids'] = json.loads(detail['dishes_ids'])
        detail['is_expired'] = self.is_expired
        return detail

    @classmethod
    def get_valid_orders(cls, **kwargs):
        kwargs['payment_status'] = 0
        kwargs['expires__gt'] = now()
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            setattr(e, 'args', ('Orders %s does not existed or is expired' % kwargs['orders_id'],))
            return e

    @classmethod
    def filter_valid_orders_detail(cls, **kwargs):
        kwargs['payment_status'] = 0
        kwargs['expires__gt'] = now()
        return cls.filter_objects_detail(**kwargs)

    @classmethod
    def filter_expired_orders_detail(cls, **kwargs):
        kwargs['payment_status'] = 0
        kwargs['expires__lte'] = now()
        return cls.filter_objects_detail(**kwargs)

    @classmethod
    def get_success_orders(cls, **kwargs):
        kwargs['payment_status'] = 200
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @property
    def dishes_ids_json_detail(self):
        import json
        return self.dishes_ids

    @classmethod
    def get_dishes_ids_detail(cls, dishes_ids):
        dishes_details = {}
        dishes_details_list = []
        food_court_id = None
        food_court_name = None
        for item in dishes_ids:
            dishes_id = item['dishes_id']
            count = item['count']
            detail_dict = Dishes.get_dishes_detail_dict_with_user_info(pk=dishes_id)
            if isinstance(detail_dict, Exception):
                raise ValueError('Dishes ID %s does not existed' % dishes_id)
            detail_dict['count'] = count

            business_list = dishes_details.get(detail_dict['business_id'], [])
            business_list.append(detail_dict)
            dishes_details[detail_dict['business_id']] = business_list
            if not food_court_id:
                food_court_id = detail_dict['food_court_id']
                food_court_name = detail_dict['food_court_name']
            if food_court_id != detail_dict['food_court_id']:
                raise ValueError('One orders cannot contain multiple food court')

        for business_id in sorted(dishes_details.keys()):
            detail_dict = {'dishes_detail': dishes_details[business_id],
                           'business_id': business_id,
                           'business_name': dishes_details[business_id][0]['business_name']}
            dishes_details_list.append(detail_dict)

        return food_court_id, food_court_name, dishes_details_list

    @classmethod
    def make_orders_by_consume(cls, request, dishes_ids):
        meal_ids = []
        total_amount = '0'
        try:
            food_court_id, food_court_name, dishes_details = \
                cls.get_dishes_ids_detail(dishes_ids)
        except Exception as e:
            return e
        for _details in dishes_details:
            for item2 in _details['dishes_detail']:
                total_amount = str(Decimal(total_amount) +
                                   Decimal(item2['price']) * item2['count'])
        # 会员优惠及其他优惠
        member_discount = 0
        other_discount = 0
        orders_data = cls.make_orders_base(request=request, food_court_id=food_court_id,
                                           food_court_name=food_court_name,
                                           dishes_details=dishes_details,
                                           total_amount=total_amount,
                                           member_discount=member_discount,
                                           other_discount=other_discount,
                                           orders_type=ORDERS_ORDERS_TYPE['online'])
        return orders_data

    @classmethod
    def make_orders_by_recharge(cls, request, orders_type, payable):
        dishes_details = [{'orders_type': orders_type,
                          'payable': payable},
                          ]
        food_court_id = 0
        food_court_name = 'CZ'
        total_amount = str(payable)

        # 会员优惠及其他优惠
        member_discount = 0
        other_discount = 0
        orders_data = cls.make_orders_base(request=request, food_court_id=food_court_id,
                                           food_court_name=food_court_name,
                                           dishes_details=dishes_details,
                                           total_amount=total_amount,
                                           member_discount=member_discount,
                                           other_discount=other_discount,
                                           orders_type=ORDERS_ORDERS_TYPE['wallet_recharge'])
        return orders_data

    @classmethod
    def make_orders_base(cls, request, food_court_id, food_court_name,
                         dishes_details, total_amount, member_discount,
                         other_discount, orders_type):
        try:
            orders_data = {'user_id': request.user.id,
                           'orders_id': OrdersIdGenerator.get_orders_id(),
                           'food_court_id': food_court_id,
                           'food_court_name': food_court_name,
                           'dishes_ids': json.dumps(dishes_details,
                                                    ensure_ascii=False, cls=DatetimeEncode),
                           'total_amount': total_amount,
                           'member_discount': str(member_discount),
                           'other_discount': str(other_discount),
                           'payable': str(Decimal(total_amount) -
                                          Decimal(member_discount) -
                                          Decimal(other_discount)),
                           'orders_type': orders_type,
                           }
        except Exception as e:
            return e
        return orders_data

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


class ConsumeOrders(models.Model):
    """
    消费订单（子订单）
    """
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=32)
    user_id = models.IntegerField('用户ID', db_index=True)

    business_name = models.CharField('商户名字', max_length=200)
    business_id = models.IntegerField('商户ID')
    food_court_id = models.IntegerField('美食城ID')
    food_court_name = models.CharField('美食城名字', max_length=200)

    dishes_ids = models.TextField('订购列表', default='')

    total_amount = models.CharField('订单总计', max_length=16)
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payable = models.CharField('应付金额', max_length=16)

    # 0:未支付 200:已支付 201:待消费 206:已完成 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=201)
    # 支付方式：0:未指定支付方式 1：钱包支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    #         201: 钱包充值订单  (预留：202：钱包消费订单 203: 钱包提现)
    orders_type = models.IntegerField('订单类型', default=ORDERS_ORDERS_TYPE['online'])
    # 所属主订单
    master_orders_id = models.CharField('所属主订单订单ID', max_length=32)
    # 是否点评过  0: 未点评过  1： 已经完成点评
    is_commented = models.IntegerField('是否点评过', default=0)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_15_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    # objects = OrdersManager()

    class Meta:
        db_table = 'ys_consume_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def is_consume_of_payment_status(cls, request, orders_id):
        kwargs = {'user_id': request.user.id,
                  'orders_id': orders_id}
        _object = cls.get_object(**kwargs)
        if isinstance(_object, Exception):
            return False
        if _object.orders_type == ORDERS_ORDERS_TYPE['online']:
            if _object.payment_status == ORDERS_PAYMENT_STATUS['consuming']:
                return True
        return False

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_detail(cls, **kwargs):
        _object = cls.get_object(**kwargs)
        if isinstance(_object, Exception):
            return _object
        result = model_to_dict(_object)
        result['dishes_ids'] = json.loads(result['dishes_ids'])
        result['trade_type'] = 'consume'
        return result

    @classmethod
    def filter_objects_detail(cls, **kwargs):
        _objects = cls.filter_objects(**kwargs)
        if isinstance(_objects, Exception):
            return _objects
        results = []
        for item in _objects:
            item_dict = model_to_dict(item)
            item_dict['dishes_ids'] = json.loads(item_dict['dishes_ids'])
            item_dict['trade_type'] = 'consume'
            item_dict['is_expired'] = None
            results.append(item_dict)
        return results

    @classmethod
    def filter_consume_objects_detail(cls, **kwargs):
        kwargs['payment_status'] = 201
        return cls.filter_objects_detail(**kwargs)

    @classmethod
    def filter_finished_objects_detail(cls, **kwargs):
        kwargs['payment_status'] = 206
        return cls.filter_objects_detail(**kwargs)


class BaseConsumeOrders(object):
    """
    子订单
    """
    def get_pay_orders_by_orders_id(self, pay_orders_id):
        return PayOrders.get_object(**{'orders_id': pay_orders_id})

    def make_consume_orders_id(self, pay_orders_id, index):
        return 'Z%s%03d' % (pay_orders_id, index)

    def create(self, pay_orders_id):
        """
        创建子订单
        return: None: 成功
                Exception：失败
        """
        from decimal import Decimal

        _instance = self.get_pay_orders_by_orders_id(pay_orders_id)
        if isinstance(_instance, Exception):
            return _instance
        pay_orders = _instance

        if pay_orders.payment_status != 200:
            return ValueError('The orders payment status must be 200!')

        orders = []
        dishes_detail_list = json.loads(pay_orders.dishes_ids)
        for index, business_dishes in enumerate(dishes_detail_list, 1):
            member_discount = 0
            other_discount = 0
            total_amount = 0
            for item in business_dishes['dishes_detail']:
                total_amount = Decimal(total_amount) + Decimal(item['price']) * item['count']
            payable = Decimal(total_amount) - Decimal(member_discount) - Decimal(other_discount)
            consume_data = {
                'orders_id': self.make_consume_orders_id(pay_orders_id, index),
                'user_id': pay_orders.user_id,
                'dishes_ids': json.dumps(business_dishes['dishes_detail']),
                'total_amount': str(total_amount),
                'member_discount': member_discount,
                'other_discount': other_discount,
                'payable': str(payable),
                'business_name': business_dishes['business_name'],
                'business_id': business_dishes['business_id'],
                'food_court_id': pay_orders.food_court_id,
                'food_court_name': pay_orders.food_court_name,
                'payment_mode': pay_orders.payment_mode,
                'orders_type': pay_orders.orders_type,
                'master_orders_id': pay_orders_id
            }
            try:
                obj = ConsumeOrders(**consume_data)
                obj.save()
            except Exception as e:
                return e
            else:
                # 同步子订单到商户端
                result = VerifyOrdersAction().create(obj)
                if isinstance(result, Exception):
                    return result
                orders.append(obj)
        return orders


class TradeRecord(models.Model):
    """
    交易记录
    """
    serial_number = models.CharField('交易流水号', db_index=True, max_length=64)
    orders_id = models.CharField('订单ID', db_index=True, max_length=32)
    user_id = models.IntegerField('用户ID')

    total_amount = models.CharField('应付金额', max_length=16)
    member_discount = models.CharField('会员优惠', max_length=16, default='0')
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payment = models.CharField('实付金额', max_length=16)

    # 支付结果: SUCCESS: 成功 FAIL：失败 UNKNOWN: 未知
    payment_result = models.CharField('支付结果', max_length=16, default='SUCCESS')
    # 支付方式：0:未指定支付方式 1：钱包支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)

    # 第三方支付订单号
    out_orders_id = models.CharField('第三方订单号', max_length=64, null=True)

    created = models.DateTimeField('创建时间', default=now)
    extend = models.TextField('扩展信息', default='', blank=True)

    class Meta:
        db_table = 'ys_trade_record'
        ordering = ['-created']

    def __unicode__(self):
        return self.serial_number


class TradeRecordAction(object):
    def verify_orders(self, request, orders):
        if request.user.id != orders.user_id:
            return False, Exception('Orders and The user do not match')
        if orders.payment_status != ORDERS_PAYMENT_STATUS['paid']:
            return False, ValueError('Orders payment status is incorrect')
        if orders.payment_mode == ORDERS_PAYMENT_MODE['unknown']:
            return False, ValueError('Orders payment mode is incorrect')
        if orders.orders_type == ORDERS_ORDERS_TYPE['unknown']:
            return False, ValueError('Orders orders type is incorrect')
        return True, None

    def create(self, request, orders, gateway='auth', **kwargs):
        """
        创建交易记录
        """
        from rest_framework.request import Request
        from django.http import HttpRequest

        if gateway == 'pay_callback':
            request = Request(HttpRequest)
            try:
                setattr(request.user, 'id', orders.user_id)
            except Exception as e:
                return e
        result, error = self.verify_orders(request, orders)
        if not result:
            return error
        record_data = {'serial_number': SerialNumberGenerator.get_serial_number(),
                       'orders_id': orders.orders_id,
                       'user_id': request.user.id,
                       'total_amount': orders.total_amount,
                       'member_discount': orders.member_discount,
                       'other_discount': orders.other_discount,
                       'payment': orders.payable,
                       'payment_mode': orders.payment_mode,
                       'out_orders_id': kwargs.get('out_orders_id'),
                       }
        try:
            obj = TradeRecord(**record_data)
            obj.save()
        except Exception as e:
            return e
        return obj


def date_for_model():
    return now().date()


class SerialNumberGenerator(models.Model):
    date = models.DateField('日期', primary_key=True, default=date_for_model)
    serial_number = models.IntegerField('订单ID', default=1)
    created = models.DateTimeField('创建日期', default=now)
    updated = models.DateTimeField('最后更改日期', auto_now=True)

    class Meta:
        db_table = 'ys_serial_number_generator'

    def __unicode__(self):
        return str(self.date)

    @classmethod
    def int_to_string(cls, serial_no):
        return "%06d" % serial_no

    @classmethod
    def get_serial_number(cls):
        date_day = date_for_model()
        # 数据库加排它锁，保证交易流水号是唯一的
        with transaction.atomic():
            try:
                _instance = cls.objects.select_for_update().get(pk=date_day)
            except cls.DoesNotExist:
                cls().save()
                serial_no = 1
            else:
                serial_no = _instance.serial_number + 1
                _instance.serial_number = serial_no
                _instance.save()
        serial_no_str = cls.int_to_string(serial_no)
        return 'LS%s%s' % (date_day.strftime('%Y%m%d'), serial_no_str)


class ConfirmConsume(models.Model):
    user_id = models.IntegerField('用户ID')
    # orders_id = models.CharField('订单ID', max_length=32)
    random_string = models.CharField('随机字符串', db_index=True, max_length=64)
    expires = models.DateTimeField('过期时间', default=main.minutes_5_plus)
    created = models.DateTimeField('创建日期', default=now)

    class Meta:
        db_table = 'ys_confirm_consume_qrcode'

    def __unicode__(self):
        return str(self.user_id)
