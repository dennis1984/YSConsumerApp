# -*- coding:utf8 -*-

from django.db import models
from django.utils.timezone import now

from horizon.models import (model_to_dict,
                            BaseManager,
                            get_perfect_filter_params)

from Admin_App.ad_coupons.models import CouponsConfig
from horizon.main import minutes_15_plus
from horizon import main
import datetime
import re
import os


class Coupons(models.Model):
    """
    我的优惠券
    """
    coupons_id = models.IntegerField(u'优惠券ID', db_index=True)
    user_id = models.IntegerField(u'用户ID')

    # 优惠券状态：1：未使用  2：已使用  400：已过期
    status = models.IntegerField(u'优惠券状态', default=1)

    created = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'更新时间', auto_now=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_coupons'

    def __unicode__(self):
        return str(self.coupons_id)

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

    @classmethod
    def get_perfect_detail_list(cls, **kwargs):
        instances = cls.filter_objects(**kwargs)
        details = []
        for instance in instances:
            consumer_detail = model_to_dict(instance)
            admin_instance = CouponsConfig.get_object(pk=instance.coupons_id)
            if isinstance(admin_instance, Exception):
                continue
            admin_detail = model_to_dict(admin_instance)
            admin_detail.pop('created')
            admin_detail.pop('updated')
            consumer_detail.update(**admin_detail)
            details.append(consumer_detail)
        return details

