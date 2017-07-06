# -*- coding:utf8 -*-
from __future__ import unicode_literals
import json
import datetime

from django.conf import settings
from horizon import redis
from django.utils.timezone import now

from Business_App.bz_dishes.models import Dishes


# 过期时间（单位：秒）
EXPIRES_24_HOURS = 24 * 60 * 60


class DishesDetailCache(object):
    def __init__(self):
        pool = redis.ConnectionPool(host=settings.REDIS_SETTINGS['host'],
                                    port=settings.REDIS_SETTINGS['port'],
                                    db=settings.REDIS_SETTINGS['db_set']['consumer'])
        self.handle = redis.Redis(connection_pool=pool)

    def get_dishes_id_key(self, dishes_id):
        return 'dishes_detail_id:%s' % dishes_id

    def set_dishes_to_cache(self, key, data):
        self.handle.set(key, data)
        self.handle.expire(key, EXPIRES_24_HOURS)

    def get_dishes_detail(self, dishes_id):
        key = self.get_dishes_id_key(dishes_id)
        instance = self.handle.get(key)
        if not instance:
            instance = Dishes.get_dishes_detail_dict_with_user_info(**{'pk': dishes_id})
            if isinstance(instance, Exception):
                return instance
            self.set_dishes_to_cache(key, instance)
        return instance
