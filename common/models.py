# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.db import transaction

from horizon import main

import json
import datetime
import copy


def date_for_model():
    return now().date()


class SerialNumberGenerator(models.Model):
    """
    交易流水号生成器
    """
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
