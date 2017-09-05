# -*- coding:utf8 -*-

from django.db import models
from django.utils.timezone import now

from horizon.models import (model_to_dict,
                            BaseManager,
                            get_perfect_filter_params)

from Admin_App.ad_coupons.models import (CouponsConfig,
                                         CouponsUsedRecord)
from users.models import ConsumerUser
from horizon.main import minutes_15_plus
from horizon import main
import datetime
import re
import os
import copy


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


class Coupons(models.Model):
    """
    我的优惠券
    """
    coupons_id = models.IntegerField(u'优惠券ID', db_index=True)
    user_id = models.IntegerField(u'用户ID')

    # 优惠券状态：1：未使用  2：已使用  400：已过期
    status = models.IntegerField(u'优惠券状态', default=1)

    expires = models.DateTimeField(u'优惠券过期时间', default=now)
    created = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'更新时间', auto_now=True)

    objects = BaseCouponsManager()

    class Meta:
        db_table = 'ys_coupons'
        ordering = ['-coupons_id']

    def __unicode__(self):
        return str(self.coupons_id)

    @property
    def is_expired(self):
        if self.status == 400:
            return True
        return False

    @classmethod
    def get_object(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_perfect_detail(cls, **kwargs):
        instance = cls.get_object(**kwargs)
        if isinstance(instance, Exception):
            return instance
        detail = model_to_dict(instance)
        admin_instance = CouponsConfig.get_object(pk=instance.coupons_id)
        if isinstance(admin_instance, Exception):
            return admin_instance

        admin_detail = model_to_dict(admin_instance)
        pop_keys = ('id', 'created', 'updated', 'expire_in', 'total_count',
                    'send_count', 'status')
        for key in pop_keys:
            admin_detail.pop(key)
        detail.update(**admin_detail)
        return detail

    @classmethod
    def get_detail_for_make_orders(cls, **kwargs):
        kwargs['expires__gt'] = now()
        return cls.get_perfect_detail(**kwargs)

    @classmethod
    def filter_objects(cls, **kwargs):
        kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.filter(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_perfect_detail_list(cls, **kwargs):
        _kwargs = copy.deepcopy(kwargs)
        if kwargs.get('status') == 400:
            kwargs['status'] = 1
            kwargs['expires__lte'] = now()
            _kwargs.pop('status')
        else:
            kwargs['expires__gt'] = now()
        instances = cls.filter_objects(**kwargs)
        details = []
        for instance in instances:
            consumer_detail = model_to_dict(instance)
            admin_instance = CouponsConfig.get_object(pk=instance.coupons_id, **_kwargs)
            if isinstance(admin_instance, Exception):
                continue

            admin_detail = model_to_dict(admin_instance)
            pop_keys = ('id', 'created', 'updated', 'expire_in', 'total_count',
                        'send_count', 'status')
            for key in pop_keys:
                admin_detail.pop(key)
            consumer_detail.update(**admin_detail)
            details.append(consumer_detail)
        return details

    @classmethod
    def update_status_for_used(cls, pk):
        """
        更新优惠券状态是为使用状态
        """
        instance = cls.get_object(pk=pk)
        if isinstance(instance, Exception):
            return instance
        try:
            instance.status = 2
            instance.save()
        except Exception as e:
            return e

        user = ConsumerUser.get_object(pk=instance.user_id)
        used_record_data = {'user_id': instance.user_id,
                            'coupons_id': instance.coupons_id,
                            'phone': user.phone}
        try:
            CouponsUsedRecord(**used_record_data).save()
        except:
            pass

        return instance

    @classmethod
    def is_used(cls, pk):
        instance = cls.get_object(pk=pk)
        if isinstance(instance, Exception):
            return True
        if instance.status == 2:
            return True
        else:
            return False
