# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.conf import settings
import os


class DishesManager(models.Manager):
    def get(self, *args, **kwargs):
        object_data = super(DishesManager, self).get(status=1, *args, **kwargs)
        return object_data

    def filter(self, *args, **kwargs):
        object_data = super(DishesManager, self).filter(status=1, *args, **kwargs)
        return object_data


DISHES_PICTURE_DIR = settings.PICTURE_DIRS['business']['dishes']


class Dishes(models.Model):
    """
    菜品信息表
    """
    title = models.CharField('菜品名称', null=False, max_length=200)
    subtitle = models.CharField('菜品副标题', max_length=200, default='')
    description = models.TextField('菜品描述', default='')
    size = models.IntegerField('菜品规格', default=10)         # 默认：10，小份：11，中份：12，大份：13
    price = models.CharField('价格', max_length=50, null=False)
    image = models.ImageField('菜品图片',
                              upload_to=DISHES_PICTURE_DIR,
                              default=os.path.join(DISHES_PICTURE_DIR, 'noImage.png'),)
    user_id = models.IntegerField('创建者ID', null=False)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    status = models.IntegerField('数据状态', default=1)   # 1 有效 2 已删除 3 其他（比如暂时不用）
    is_recommend = models.BooleanField('是否推荐该菜品', default=False)   # 0: 不推荐  1：推荐
    extend = models.TextField('扩展信息', default='', blank=True)

    # objects = models.Manager()
    # active_objects = DishesManager()
    objects = DishesManager()

    class Meta:
        db_table = 'ys_dishes'
        unique_together = ('title', 'user_id', 'size')

    def __unicode__(self):
        return self.title

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_list(cls, request, **kwargs):
        # 如果是用户是admin并且过滤条件为空，则返回所有菜品
        # 否则返回过滤条件中对应用户的所有菜品
        # 如果是商户，则返回当前用户的所有菜品
        if request.user.is_admin:
            if 'user_id' not in kwargs:
                return cls.objects.all()
            else:
                filter_dict = {'user_id': kwargs['user_id']}
        else:
            filter_dict = {'user_id': request.user.id}

        try:
            return cls.objects.filter(**filter_dict)
        except Exception as e:
            return e


class FoodCourt(models.Model):
    """
    美食城数据表
    """
    name = models.CharField('美食城名字', max_length=200)
    city = models.CharField('所属城市', max_length=100, null=False)
    district = models.CharField('所属市区', max_length=100, null=False)
    mall = models.CharField('所属购物中心', max_length=200, default='')
    extend = models.TextField('扩展信息', default='', blank=True, null=True)

    class Meta:
        db_table = 'ys_food_court'
        unique_together = ('name', 'mall')

    def __unicode__(self):
        return self.name

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except Exception as e:
            return e

    @classmethod
    def get_object_list(cls, **kwargs):
        if 'page_size' in kwargs:
            kwargs.pop('page_size')
        if 'page_index' in kwargs:
            kwargs.pop('page_index')
        return cls.objects.filter(**kwargs)
