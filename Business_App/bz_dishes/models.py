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
}
DISHES_MARK_DISCOUNT_VALUES = (10, 20, 30)
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

    # 运营标记： 0：无标记  10：新品  20：特惠  30：招牌
    mark = models.IntegerField('运营标记', default=0)
    # 优惠金额
    discount = models.CharField('优惠金额', max_length=16, default='0')

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
        hot_objects = cls.filter_objects(**kwargs)
        if isinstance(hot_objects, Exception):
            return hot_objects

        hot_objects = sorted(hot_objects, key=lambda x: x['sort_orders'])

        dishes_list = []
        for item in hot_objects:
            dishes = cls.get_dishes_detail_dict_with_user_info(pk=item.pk)
            dishes_list.append(dishes)
        return dishes_list

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
        dishes_dict['business_name'] = getattr(user, 'business_name', '')
        dishes_dict['business_id'] = dishes_dict['user_id']
        if dishes_dict['mark'] in DISHES_MARK_DISCOUNT_VALUES:
            dishes_dict['discount_price'] = str(Decimal(instance.price) -
                                                Decimal(instance.discount))
        else:
            dishes_dict['discount_price'] = instance.price

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
