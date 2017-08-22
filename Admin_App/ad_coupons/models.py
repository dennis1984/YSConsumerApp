# -*- coding:utf8 -*-

from django.db import models
from django.utils.timezone import now

from horizon.models import (model_to_dict,
                            BaseManager,
                            get_perfect_filter_params)
from horizon.main import minutes_15_plus
from horizon import main
import datetime
import re
import os


COUPONS_CONFIG_TYPE = {
    'member': 10,       # 会员优惠
    'online': 20,       # 在线下单优惠
    'other': 100,       # 其它优惠
    'custom': 200,      # 自定义
}

COUPONS_CONFIG_TYPE_CN_MATCH = {
    10: u'会员优惠',
    20: u'在线下单优惠',
    100: u'其它优惠',
    200: u'自定义',
    }

COUPONS_CONFIG_FUZZY_FIELDS = ('name', 'type_detail')


class BaseCouponsManager(models.Manager):
    def get(self, *args, **kwargs):
        if 'status' not in kwargs:
            kwargs['status'] = 1
        instance = super(BaseCouponsManager, self).get(*args, **kwargs)
        if now() >= instance.expires:
            instance.status = 400
        return instance

    def filter(self, *args, **kwargs):
        if 'status' not in kwargs:
            kwargs['status'] = 1
        instances = super(BaseCouponsManager, self).filter(*args, **kwargs)
        for instance in instances:
            if now() >= instance.expires:
                instance.status = 400
        return instances


class CouponsConfig(models.Model):
    """
    优惠券配置
    """
    name = models.CharField(u'优惠券名称', max_length=64)

    # 优惠券类别：会员优惠：10， 在线下单优惠：20，其它优惠：100，自定义：200
    type = models.IntegerField(u'优惠券类别')
    type_detail = models.CharField(u'优惠券类别详情', max_length=64)

    amount_of_money = models.CharField(u'优惠金额', max_length=16)
    service_ratio = models.IntegerField(u'平台商承担（优惠）比例')
    business_ratio = models.IntegerField(u'商户承担（优惠）比例')

    expires = models.DateTimeField(u'优惠券失效日期', default=main.days_7_plus)
    # 数据状态：1：正常 400：已过期 其它值：已删除
    status = models.IntegerField(u'数据状态', default=1)
    created = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'最后更新时间', auto_now=True)

    objects = BaseCouponsManager()

    class Meta:
        db_table = 'ys_coupons_config'
        unique_together = ('type_detail', 'name', 'status')
        app_label = 'Admin_App.ad_coupons.models.CouponsConfig'

    @classmethod
    def get_object(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_active_object(cls, **kwargs):
        kwargs['expires__gt'] = now()
        return cls.get_object(**kwargs)


    @classmethod
    def filter_objects(cls, fuzzy=False, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        if fuzzy:
            for key in COUPONS_CONFIG_FUZZY_FIELDS:
                if key in kwargs:
                    kwargs['%s__contains' % key] = kwargs.pop(key)
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e
