# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from django.conf import settings
from Business_App.bz_users.models import BusinessUser, FoodCourt
from horizon.models import model_to_dict
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
    # 默认：10，小份：11，中份：12，大份：13，自定义：20
    size = models.IntegerField('菜品规格', default=10)
    size_detail = models.CharField('菜品规格详情', max_length=30, null=True, blank=True)
    price = models.CharField('价格', max_length=50, null=False, blank=False)
    image = models.ImageField('菜品图片',
                              upload_to=DISHES_PICTURE_DIR,
                              default=os.path.join(DISHES_PICTURE_DIR, 'noImage.png'),)
    user_id = models.IntegerField('创建者ID', null=False)
    food_court_id = models.IntegerField('商城ID', db_index=True)
    created = models.DateTimeField('创建时间', default=now)
    updated = models.DateTimeField('最后修改时间', auto_now=True)
    status = models.IntegerField('数据状态', default=1)   # 1 有效 2 已删除 3 其他（比如暂时不用）
    is_recommend = models.BooleanField('是否推荐该菜品', default=False)   # 0: 不推荐  1：推荐
    extend = models.TextField('扩展信息', default='', blank=True)

    objects = DishesManager()

    class Meta:
        db_table = 'ys_dishes'
        unique_together = ('user_id', 'title', 'size',
                           'size_detail', 'status')
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
    def get_hot_sale_object(cls, **kwargs):
        try:
            dishes = cls.objects.get(**kwargs)
            dishes_detail = cls.get_dishes_detail_dict_with_user_info(pk=dishes.pk)
            return dishes_detail
        except Exception as e:
            return e

    @classmethod
    def get_hot_sale_list(cls, request, **kwargs):
        filter_dict = {'food_court_id': kwargs['food_court_id'],
                       'is_recommend': 1}
        try:
            hot_objects = cls.objects.filter(**filter_dict)
            dishes_list = []
            for item in hot_objects:
                dishes = cls.get_dishes_detail_dict_with_user_info(pk=item.pk)
                dishes_list.append(dishes)

            return dishes_list
        except Exception as e:
            return e

    @classmethod
    def get_dishes_detail_dict_with_user_info(cls, **kwargs):
        instance = cls.get_object(**kwargs)
        if isinstance(instance, Exception):
            return instance
        user = BusinessUser.get_object(pk=instance.user_id)
        dishes_dict = model_to_dict(instance)
        dishes_dict['business_name'] = getattr(user, 'business_name', '')
        dishes_dict['business_id'] = dishes_dict['user_id']

        base_dir = str(dishes_dict['image']).split('static', 1)[1]
        if base_dir.startswith(os.path.sep):
            base_dir = base_dir[1:]
        dishes_dict.pop('image')
        dishes_dict['image_url'] = os.path.join(settings.WEB_URL_FIX,
                                                'static',
                                                base_dir)
        # 获取美食城信息
        food_instance = FoodCourt.get_object(pk=user.food_court_id)
        dishes_dict['food_court_name'] = getattr(food_instance, 'name', '')
        dishes_dict['food_court_id'] = getattr(food_instance, 'id', None)

        return dishes_dict
