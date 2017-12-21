# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.conf import settings
from Business_App.bz_users.models import BusinessUser, FoodCourt
from horizon.models import (model_to_dict,
                            BaseManager,
                            get_perfect_filter_params,
                            get_perfect_detail_by_instance)

from django.conf import settings
from decimal import Decimal
import os

DISHES_MARK = {
    'default': 0,
    'new': 10,
    'preferential': 20,
    'flagship': 30,
    'new_business': 40,
    'night_discount': 50,
}
DISHES_MARK_DISCOUNT_VALUES = (10, 20, 30, 40, 50)
CAN_NOT_USE_COUPONS_WITH_MARK = [DISHES_MARK['new_business']]
DISHES_FOR_NIGHT_DISCOUNT = [DISHES_MARK['night_discount']]
DISHES_PICTURE_DIR = settings.PICTURE_DIRS['business']['dishes']


class Dishes(models.Model):
    """
    菜品信息表
    """
    title = models.CharField('菜品名称', null=False, max_length=40)
    subtitle = models.CharField('菜品副标题', max_length=100, default='')
    description = models.TextField('菜品描述', default='')
    # 默认：10，小份：11，中份：12，大份：13，自定义：20
    size = models.IntegerField('菜品规格', default=10)
    size_detail = models.CharField('菜品规格详情', max_length=30, null=True, blank=True)
    price = models.CharField('价格', max_length=16, null=False, blank=False)
    image = models.ImageField('菜品图片（封面）',
                              upload_to=DISHES_PICTURE_DIR,
                              default=os.path.join(DISHES_PICTURE_DIR, 'noImage.png'), )
    image_detail = models.ImageField('菜品图片（详情）',
                                     upload_to=DISHES_PICTURE_DIR,
                                     default=os.path.join(DISHES_PICTURE_DIR, 'noImage.png'), )
    user_id = models.IntegerField('创建者ID', db_index=True)
    food_court_id = models.IntegerField('商城ID', db_index=True)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    status = models.IntegerField('数据状态', default=1)  # 1 有效 2 已删除 3 其他（比如暂时不用）
    is_recommend = models.BooleanField('是否推荐该菜品', default=False)  # 0: 不推荐  1：推荐

    # 运营标记： 0：无标记  10：新品  20：特惠  30：招牌  40: 新商户专区  50: 晚市特惠
    mark = models.IntegerField('运营标记', default=0)
    # 优惠金额
    discount = models.CharField('优惠金额', max_length=16, default='0')
    # 优惠时间段-开始 (用来标记菜品在某个时段是否有优惠)，以24小时制数字为标准， 如：8:00（代表早晨8点）
    discount_time_slot_start = models.CharField('优惠时间段-开始', max_length=16, null=True)
    # 优惠时间段-结束 (用来标记菜品在某个时段是否有优惠)，以24小时制数字为标准， 如：19:30（代表晚上7点30分）
    discount_time_slot_end = models.CharField('优惠时间段-结束', max_length=16, null=True)

    # 菜品标记和排序顺序
    tag = models.CharField('标记', max_length=64, default='', null=True, blank=True)
    sort_orders = models.IntegerField('排序标记', default=None, null=True)

    extend = models.TextField('扩展信息', default='', null=True, blank=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_dishes'
        unique_together = ('user_id', 'title', 'size',
                           'size_detail', 'status')
        ordering = ['-updated']
        app_label = 'Business_App.bz_dishes.models.Dishes'

    def __unicode__(self):
        return self.title

    @classmethod
    def get_object(cls, **kwargs):
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
    def get_hot_sale_object(cls, **kwargs):
        try:
            dishes = cls.objects.get(**kwargs)
            dishes_detail = cls.get_dishes_detail_dict_with_user_info(pk=dishes.pk)
            return dishes_detail
        except Exception as e:
            return e

    @classmethod
    def get_hot_sale_list(cls, request, **kwargs):
        if 'mark' not in kwargs and 'mark__in' not in kwargs:
            kwargs['mark__in'] = DISHES_MARK_DISCOUNT_VALUES
        hot_objects = cls.filter_objects(**kwargs)
        if isinstance(hot_objects, Exception):
            return hot_objects

        hot_objects = sorted(hot_objects, key=lambda x: x.sort_orders)
        dishes_list = []
        for item in hot_objects:
            dishes = cls.get_dishes_detail_dict_with_user_info(pk=item.pk)
            dishes_list.append(dishes)
        return dishes_list

    @classmethod
    def is_sale_time_slot(cls, dishes_object):
        """
        判断当前时间是否在菜品优惠时段内
        返回：True 或 False
        """
        if isinstance(dishes_object, cls):
            mark = dishes_object.mark
            discount_time_slot_start = dishes_object.discount_time_slot_start
            discount_time_slot_end = dishes_object.discount_time_slot_end
        else:
            mark = dishes_object['mark']
            discount_time_slot_start = dishes_object['discount_time_slot_start']
            discount_time_slot_end = dishes_object['discount_time_slot_end']

        if mark in DISHES_FOR_NIGHT_DISCOUNT:
            start_hour_str, start_second_str = discount_time_slot_start.split(':')
            end_hour_str, end_second_str = discount_time_slot_end.split(':')
            time_start_int = int('%02d%02d' % (int(start_hour_str), int(start_second_str)))
            time_end_int = int('%02d%02d' % (int(end_hour_str), int(end_second_str)))
            time_now = now()
            time_now_hour_minute_int = int('%02d%02d' % (time_now.hour, time_now.minute))
            if time_start_int < time_now_hour_minute_int < time_end_int:
                return True
            else:
                return False
        else:
            return True

    @classmethod
    def get_dishes_detail_dict_with_user_info(cls, need_perfect=False,  **kwargs):
        instance = cls.get_object(**kwargs)
        if isinstance(instance, Exception):
            return instance

        user = BusinessUser.get_object(pk=instance.user_id)
        if need_perfect:
            dishes_dict = get_perfect_detail_by_instance(instance)
        else:
            dishes_dict = model_to_dict(instance)
        # # 判断价格是否是优惠时段
        # is_sale_time = cls.is_sale_time_slot(instance)
        # if not is_sale_time:
        #     dishes_dict['discount'] = 0
        dishes_dict['business_name'] = getattr(user, 'business_name', '')
        dishes_dict['stalls_number'] = user.stalls_number
        dishes_dict['business_id'] = dishes_dict['user_id']
        if dishes_dict['mark'] in DISHES_MARK_DISCOUNT_VALUES:
            dishes_dict['discount_price'] = str(Decimal(dishes_dict['price']) -
                                                Decimal(dishes_dict['discount']))
        else:
            dishes_dict['discount_price'] = dishes_dict['price']

        # 获取美食城信息
        food_instance = FoodCourt.get_object(pk=user.food_court_id)
        dishes_dict['food_court_name'] = getattr(food_instance, 'name', '')
        dishes_dict['food_court_id'] = getattr(food_instance, 'id', None)

        return dishes_dict


class City(models.Model):
    """
    城市信息
    """
    city = models.CharField('城市名称', max_length=40, db_index=True)
    # 市区数据结构：
    # [{'id': 1, 'name': u'大兴区'}, ...
    # ]
    district = models.CharField('市区信息', max_length=40)

    user_id = models.IntegerField('创建者')
    # 城市信息状态：1：有效 2：已删除
    status = models.IntegerField('数据状态', default=1)
    created = models.DateTimeField(default=now)
    updated = models.DateTimeField(auto_now=True)

    objects = BaseManager()

    class Meta:
        db_table = 'ys_city'
        ordering = ['city', 'district']
        unique_together = ('city', 'district', 'status')
        app_label = 'Business_App.bz_dishes.models.City'

    def __unicode__(self):
        return self.city

    @classmethod
    def get_object(cls, **kwargs):
        _kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.get(**_kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_objects(cls, **kwargs):
        _kwargs = get_perfect_filter_params(cls, **kwargs)
        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e

    @classmethod
    def filter_details(cls, **kwargs):
        instances = cls.filter_objects(**kwargs)
        if isinstance(instances, Exception):
            return instances

        return [model_to_dict(ins) for ins in instances]
