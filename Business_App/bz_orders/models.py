# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.timezone import now
from django.db import transaction


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
        with transaction.atomic(using='business'):   # 多数据库事务管理需显示声明操作的数据库（以后的版本可能会改进）
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
