# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.timezone import now
from django.db import transaction
from horizon.main import minutes_15_plus
from horizon.models import model_to_dict


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
        app_label = 'Business_App.bz_orders.models.OrdersIdGenerator'

    def __unicode__(self):
        return str(self.date)

    @classmethod
    def get_orders_id(cls):
        date_day = date_for_model()
        orders_id = 0
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
    核销订单
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
    other_discount = models.CharField('其他优惠', max_length=16, default='0')
    payable = models.CharField('应付金额', max_length=16)

    # 0:未支付 200:已支付 201:待消费 206:已完成 400: 已过期 500:支付失败
    payment_status = models.IntegerField('订单支付状态', default=201)
    # 支付方式：0:未指定支付方式 1：钱包支付 2：微信支付 3：支付宝支付
    payment_mode = models.IntegerField('订单支付方式', default=0)
    # 订单类型 0: 未指定 101: 在线订单 102：堂食订单 103：外卖订单
    orders_type = models.IntegerField('订单类型', default=101)

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


class VerifyOrdersAction(object):
    """
    核销订单
    """
    def is_valid_consume_orders(self, consume_orders):
        if consume_orders.payment_status != ORDERS_PAYMENT_STATUS['consuming'] or\
                        consume_orders.orders_type != ORDERS_ORDERS_TYPE['online']:
            return False, Exception('Orders data is incorrect')
        return True, None

    def create(self, consume_orders):
        """
        创建核销订单
        return: None: 成功
                Exception：失败
        """
        is_valid, result = self.is_valid_consume_orders(consume_orders)
        if not is_valid:
            return result

        orders_data = model_to_dict(consume_orders)
        pop_keys = ['created', 'updated', 'master_orders_id', 'is_commented']
        for key in pop_keys:
            orders_data.pop(key)
        consumer_id = orders_data['user_id']
        business_id = orders_data['business_id']
        orders_data['user_id'] = business_id
        orders_data['consumer_id'] = consumer_id
        orders_data.pop('business_id')

        try:
            obj = VerifyOrders(**orders_data)
            obj.save()
        except Exception as e:
            return e
        return obj
