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
    # 订单类型 1: 在线订单 2：线下订单
    orders_status = models.IntegerField('订单类型', default=1)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_30_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = OrdersManager()

    class Meta:
        db_table = 'ys_pay_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_valid_orders(cls, **kwargs):
        kwargs['payment_status'] = 0
        kwargs['expires__gt'] = now()
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            e.args = ('Orders %s does not existed or is expired',)
            return e

    @classmethod
    def get_dishes_ids_detail(cls, request, dishes_ids):
        dishes_details = {}
        food_court_id = None
        food_court_name = None
        for item in dishes_ids:
            dishes_id = item['dishes_id']
            count = item['count']
            detail_dict = Dishes.get_dishes_detail_dict_with_user_info(pk=dishes_id)
            if isinstance(detail_dict, Exception):
                raise ValueError('Dishes ID %s does not existed' % dishes_id)
            detail_dict['count'] = count

            food_court_dict = dishes_details.get(detail_dict['food_court_id'], {})
            business_list = food_court_dict.get(detail_dict['business_id'], [])
            business_list.append(detail_dict)
            food_court_dict[detail_dict['business_id']] = business_list
            dishes_details[detail_dict['food_court_id']] = food_court_dict
            if not food_court_id:
                food_court_id = detail_dict['food_court_id']
                food_court_name = detail_dict['food_court_name']

        return food_court_id, food_court_name, dishes_details

    @classmethod
    def make_orders_by_dishes_ids(cls, request, dishes_ids):
        meal_ids = []
        total_amount = '0'
        try:
            food_court_id, food_court_name, dishes_details = \
                cls.get_dishes_ids_detail(request, dishes_ids)
        except Exception as e:
            return e
        for bz_item in dishes_details.values():
            for bz_id, _details in bz_item.items():
                for item2 in _details:
                    total_amount = str(Decimal(total_amount) +
                                       Decimal(item2['price']) * item2['count'])
        # 会员优惠及其他优惠
        member_discount = 0
        other_discount = 0
        orders_data = {'user_id': request.user.id,
                       'orders_id': OrdersIdGenerator.get_orders_id(),
                       'food_court_id': food_court_id,
                       'food_court_name': food_court_name,
                       'dishes_ids': json.dumps(dishes_details, ensure_ascii=False, cls=DatetimeEncode),
                       'total_amount': total_amount,
                       'member_discount': str(member_discount),
                       'other_discount': str(other_discount),
                       'payable': str(Decimal(total_amount) -
                                      Decimal(member_discount) -
                                      Decimal(other_discount))
                       }
        return orders_data


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
    # 支付方式：0:未指定支付方式 1：现金支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 1: 在线订单 2：线下订单
    orders_status = models.IntegerField('订单类型', default=1)
    # 所属主订单
    master_orders_id = models.CharField('所属主订单订单ID', max_length=32)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_30_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = OrdersManager()

    class Meta:
        db_table = 'ys_consume_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

#     @classmethod
#     def get_dishes_by_id(cls, pk):
#         try:
#             return Dishes.objects.get(pk=pk)
#         except Exception as e:
#             return e
#
#     @classmethod
#     def make_orders_by_dishes_ids(cls, request, dishes_ids):
#         meal_ids = []
#         total_payable = '0'
#         for item in dishes_ids:
#             object_data = cls.get_dishes_by_id(item['dishes_id'])
#             if isinstance(object_data, Exception):
#                 return object_data
#
#             object_dict = model_to_dict(object_data)
#             object_dict['count'] = item['count']
#             meal_ids.append(object_dict)
#             total_payable = str(Decimal(total_payable) + Decimal(object_data.price) * item['count'])
#
#         food_court_obj = FoodCourt.get_object(pk=request.user.food_court_id)
#         if isinstance(food_court_obj, Exception):
#             return food_court_obj
#
#         orders_data = {'user_id': request.user.id,
#                        'orders_id': OrdersIdGenerator.get_orders_id(),
#                        'food_court_name': food_court_obj.name,
#                        'city': food_court_obj.city,
#                        'district': food_court_obj.district,
#                        'mall': food_court_obj.mall,
#                        'dishes_ids': json.dumps(meal_ids, ensure_ascii=False, cls=DatetimeEncode),
#                        'payable': total_payable,
#                        }
#         return orders_data
#
#     @property
#     def dishes_ids_json_detail(self):
#         import json
#         results = self.dishes_ids_detail
#         return json.dumps(results)
#
#     @property
#     def dishes_ids_detail(self):
#         results = []
#         instance_list = json.loads(self.dishes_ids)
#         for _instance in instance_list:
#             _ins_dict = {'count': _instance['count'],
#                          'id': _instance['id'],
#                          'is_recommend': _instance['is_recommend'],
#                          'price': _instance['price'],
#                          'size': _instance['size'],
#                          'title': _instance['title'],
#                          'user_id': _instance['user_id']}
#             results.append(_ins_dict)
#         return results
#
#     @classmethod
#     def get_object(cls, *args, **kwargs):
#         try:
#             return cls.objects.get(**kwargs)
#         except Exception as e:
#             return e
#
#     @classmethod
#     def get_object_by_orders_id(cls, orders_id):
#         try:
#             return cls.objects.get(orders_id=orders_id)
#         except Exception as e:
#             return e
#
#     @classmethod
#     def get_objects_list(cls, request, **kwargs):
#         opts = cls._meta
#         fields = []
#         for f in opts.concrete_fields:
#             fields.append(f.name)
#
#         _kwargs = {}
#         if request.user.is_admin:
#             if 'user_id' in kwargs:
#                 _kwargs['user_id'] = kwargs['user_id']
#         else:
#             _kwargs['user_id'] = request.user.id
#         if 'start_created' in kwargs:
#             _kwargs['created__gte'] = kwargs['start_created']
#         if 'end_created' in kwargs:
#             _kwargs['created__lte'] = kwargs['end_created']
#         for key in kwargs:
#             if key in fields:
#                 _kwargs[key] = kwargs[key]
#
#         try:
#             return cls.objects.filter(**_kwargs)
#         except Exception as e:
#             return e
#
#     @classmethod
#     def update_payment_status_by_pay_callback(cls, orders_id, validated_data):
#         if not isinstance(validated_data, dict):
#             raise ValueError('Parameter error')
#
#         payment_status = validated_data.get('payment_status')
#         payment_mode = validated_data.get('payment_mode')
#         if payment_status not in (200, 400, 500):
#             raise ValueError('Payment status must in range [200, 400, 500]')
#         if payment_mode not in [2, 3]:    # 微信支付和支付宝支付
#             raise ValueError('Payment mode must in range [2, 3]')
#         instance = None
#         # 数据库加排它锁，保证更改信息是列队操作的，防止数据混乱
#         with transaction.atomic():
#             try:
#                 _instance = cls.objects.select_for_update().get(orders_id=orders_id)
#             except cls.DoesNotExist:
#                 raise cls.DoesNotExist
#             if _instance.payment_status != 0:
#                 raise Exception('Cannot perform this action')
#             _instance.payment_status = payment_status
#             _instance.payment_mode = payment_mode
#             _instance.save()
#             instance = _instance
#         return instance
