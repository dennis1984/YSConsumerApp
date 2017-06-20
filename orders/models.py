# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
# from bz_dishes.models import Dishes, FoodCourt
from users.models import ConsumerUser
from horizon.models import model_to_dict
from horizon.main import minutes_30_plus
from django.db import transaction
from decimal import Decimal

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


class Orders(models.Model):
    orders_id = models.CharField('订单ID', db_index=True, unique=True, max_length=30)
    user_id = models.IntegerField('用户ID', db_index=True)
    food_court_name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')

    dishes_ids = models.TextField('订购列表', default='')
    payable = models.CharField('订单总计', max_length=50, default='')

    # 0:未支付 200:已支付 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=0)
    # 支付方式：0:未指定支付方式 1：现金支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)

    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    expires = models.DateTimeField('订单过期时间', default=minutes_30_plus)
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = OrdersManager()

    class Meta:
        db_table = 'ys_orders'
        ordering = ['-orders_id']

    def __unicode__(self):
        return self.orders_id

    @classmethod
    def get_dishes_by_id(cls, pk):
        try:
            return Dishes.objects.get(pk=pk)
        except Exception as e:
            return e

    @classmethod
    def make_orders_by_dishes_ids(cls, request, dishes_ids):
        meal_ids = []
        total_payable = '0'
        for item in dishes_ids:
            object_data = cls.get_dishes_by_id(item['dishes_id'])
            if isinstance(object_data, Exception):
                return object_data

            object_dict = model_to_dict(object_data)
            object_dict['count'] = item['count']
            meal_ids.append(object_dict)
            total_payable = str(Decimal(total_payable) + Decimal(object_data.price) * item['count'])

        food_court_obj = FoodCourt.get_object(pk=request.user.food_court_id)
        if isinstance(food_court_obj, Exception):
            return food_court_obj

        orders_data = {'user_id': request.user.id,
                       'orders_id': OrdersIdGenerator.get_orders_id(),
                       'food_court_name': food_court_obj.name,
                       'city': food_court_obj.city,
                       'district': food_court_obj.district,
                       'mall': food_court_obj.mall,
                       'dishes_ids': json.dumps(meal_ids, ensure_ascii=False, cls=DatetimeEncode),
                       'payable': total_payable,
                       }
        return orders_data

    @property
    def dishes_ids_json_detail(self):
        import json
        results = self.dishes_ids_detail
        return json.dumps(results)

    @property
    def dishes_ids_detail(self):
        results = []
        instance_list = json.loads(self.dishes_ids)
        for _instance in instance_list:
            _ins_dict = {'count': _instance['count'],
                         'id': _instance['id'],
                         'is_recommend': _instance['is_recommend'],
                         'price': _instance['price'],
                         'size': _instance['size'],
                         'title': _instance['title'],
                         'user_id': _instance['user_id']}
            results.append(_ins_dict)
        return results

    @classmethod
    def get_object(cls, *args, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_by_orders_id(cls, orders_id):
        try:
            return cls.objects.get(orders_id=orders_id)
        except Exception as e:
            return e

    @classmethod
    def get_objects_list(cls, request, **kwargs):
        opts = cls._meta
        fields = []
        for f in opts.concrete_fields:
            fields.append(f.name)

        _kwargs = {}
        if request.user.is_admin:
            if 'user_id' in kwargs:
                _kwargs['user_id'] = kwargs['user_id']
        else:
            _kwargs['user_id'] = request.user.id
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = kwargs['end_created']
        for key in kwargs:
            if key in fields:
                _kwargs[key] = kwargs[key]

        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e

    @classmethod
    def update_payment_status_by_pay_callback(cls, orders_id, validated_data):
        if not isinstance(validated_data, dict):
            raise ValueError('Parameter error')

        payment_status = validated_data.get('payment_status')
        payment_mode = validated_data.get('payment_mode')
        if payment_status not in (200, 400, 500):
            raise ValueError('Payment status must in range [200, 400, 500]')
        if payment_mode not in [2, 3]:    # 微信支付和支付宝支付
            raise ValueError('Payment mode must in range [2, 3]')
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


def get_sale_list(request, **kwargs):
    if request.user.is_admin and 'user_id' not in kwargs:
        return get_sale_list_by_admin(request, **kwargs)
    else:
        return get_sale_list_by_user(request, **kwargs)


def get_sale_list_by_user(request, **kwargs):
    """
    销售统计（普通用户）
    """
    # 支付状态为：已支付
    kwargs['payment_status'] = 200
    # 如果参数没有选择时间范围，默认选取当前时间至向前30天的数据
    if not ('start_created' in kwargs or 'end_created' in kwargs):
        kwargs['start_created'] = now().date() - datetime.timedelta(days=30)
        kwargs['end_created'] = now().date()
    orders_list = Orders.get_objects_list(request, **kwargs)
    if isinstance(orders_list, Exception):
        return orders_list

    sale_dict = {}
    for item in orders_list:
        datetime_day = item.created.date()
        sale_detail = sale_dict.get(datetime_day, {'total_count': 0, 'total_payable': '0'})
        sale_detail['total_count'] += 1
        sale_detail['total_payable'] = Decimal(sale_detail['total_payable']) + Decimal(item.payable)
        sale_dict[datetime_day] = sale_detail
    results = []
    for key, value in sale_dict.items():
        sale_detail = value
        sale_detail['date'] = str(key)
        sale_detail['total_payable'] = str(sale_detail['total_payable'])
        results.append(sale_detail)
    results.sort(key=lambda x: x['date'], reverse=True)
    return results


def get_sale_list_by_admin(request, **kwargs):
    """
    销售统计（管理员）
    """
    # 支付状态为：已支付
    kwargs['payment_status'] = 200
    # 如果参数没有选择时间范围，默认选取当前时间至向前30天的数据
    if not ('start_created' in kwargs or 'end_created' in kwargs):
        kwargs['start_created'] = now().date() - datetime.timedelta(days=30)
        kwargs['end_created'] = now().date()
    orders_list = Orders.get_objects_list(request, **kwargs)
    if isinstance(orders_list, Exception):
        return orders_list

    users_list = BusinessUser.objects.all()
    users_dict = {item.id: item for item in users_list}

    sale_dict = {}
    for item in orders_list:
        user_obj = users_dict.get(item.user_id)
        business_name = getattr(user_obj, 'business_name', 'none')
        sale_detail = sale_dict.get(business_name, {'total_count': 0,
                                                    'total_payable': '0',
                                                    'user_id': item.user_id,
                                                    'start_created': now().date(),
                                                    })
        if item.created.date() < sale_detail['start_created']:
            sale_detail['start_created'] = item.created.date()
        sale_detail['total_count'] += 1
        sale_detail['total_payable'] = Decimal(sale_detail['total_payable']) + Decimal(item.payable)
        sale_dict[business_name] = sale_detail
    results = []
    for key, value in sale_dict.items():
        sale_detail = value
        sale_detail['date'] = '%s--%s' % (kwargs.get('start_created', sale_detail['start_created']),
                                          kwargs.get('end_created', now().date()))
        sale_detail['business_name'] = key
        sale_detail['total_payable'] = str(sale_detail['total_payable'])
        results.append(sale_detail)
    results.sort(key=lambda x: x['business_name'], reverse=True)
    return results


def date_for_model():
    return now().date()


def ordersIdIntegerToString(orders_id):
    return "%06d" % orders_id


class OrdersIdGenerator(models.Model):
    date = models.DateField('日期', primary_key=True, default=date_for_model)
    orders_id = models.IntegerField('订单ID', default=1)
    created = models.DateTimeField('创建日期', default=now)
    updated = models.DateTimeField('最后更改日期', auto_now=True)

    class Meta:
        db_table = 'ys_orders_id_generator'

    def __unicode__(self):
        return str(self.date)

    @classmethod
    def get_orders_id(cls):
        date_day = date_for_model()
        orders_id = 0
        # 数据库加排它锁，保证订单号是唯一的
        with transaction.atomic():
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


class DatetimeEncode(json.JSONEncoder):
    def default(self, o):
        from django.db.models.fields.files import ImageFieldFile

        if isinstance(o, datetime.datetime):
            return str(o)
        elif isinstance(o, ImageFieldFile):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)

