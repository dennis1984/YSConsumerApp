# -*- coding:utf8 -*-
from __future__ import unicode_literals
import json
import datetime

from django.conf import settings
from horizon import redis
from django.utils.timezone import now

from Business_App.bz_dishes.models import Dishes, DISHES_MARK_DISCOUNT_VALUES


# 过期时间（单位：秒）
EXPIRE_SECONDS = 10 * 60 * 60
EXPIRE_24_HOURS = 24 * 60 * 60


class HotSaleCache(object):
    def __init__(self):
        pool = redis.ConnectionPool(host=settings.REDIS_SETTINGS['host'],
                                    port=settings.REDIS_SETTINGS['port'],
                                    db=settings.REDIS_SETTINGS['db_set']['consumer'])
        self.handle = redis.Redis(connection_pool=pool)

    def get_hot_sale_list_key(self, food_court_id=1, mark=10):
        return 'hot_sale_id_key:food_court_id:%s:mark:%s' % (food_court_id, mark)

    def set_hot_sale_list(self, key, dishes_list):
        self.handle.delete(key)
        self.handle.rpush(key, *dishes_list)
        self.handle.expire(key, EXPIRE_24_HOURS)

    def get_list_data_from_cache(self, key):
        return self.handle.lrange(key)

    def get_hot_sale_list(self, food_court_id=1, mark=10):
        key = self.get_hot_sale_list_key(food_court_id, mark)
        hot_list = self.get_list_data_from_cache(key)
        if not hot_list:
            if mark == 0:
                kwargs = {'food_court_id': food_court_id,
                          'mark__in': DISHES_MARK_DISCOUNT_VALUES}
            else:
                kwargs = {'food_court_id': food_court_id,
                          'mark': mark}
            hot_list = Dishes.get_hot_sale_list(None, **kwargs)
            self.set_hot_sale_list(key, hot_list)
            return hot_list
        return hot_list

