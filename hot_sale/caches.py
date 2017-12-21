# -*- coding:utf8 -*-
from __future__ import unicode_literals
import json
import datetime

from django.conf import settings
from horizon import redis
from django.utils.timezone import now

from Business_App.bz_dishes.models import (Dishes,
                                           DISHES_MARK_DISCOUNT_VALUES,
                                           )
from decimal import Decimal


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

    def get_dishes_id_key(self, dishes_id):
        return 'dishes_detail_id:%s' % dishes_id

    def set_hot_sale_list(self, key, dishes_list):
        self.handle.delete(key)
        self.handle.rpush(key, *dishes_list)
        self.handle.expire(key, EXPIRE_24_HOURS)

    def set_data_to_cache(self, key, data):
        self.handle.set(key, data)
        self.handle.expire(key, EXPIRE_24_HOURS)

    def get_list_data_from_cache(self, key):
        return self.handle.lrange(key)

    def get_perfect_dishes_detail(self, dishes_detail):
        # 判断价格是否是优惠时段
        is_sale_time = Dishes.is_sale_time_slot(dishes_detail)
        if not is_sale_time:
            dishes_detail['discount'] = 0
        if dishes_detail['mark'] in DISHES_MARK_DISCOUNT_VALUES:
            dishes_detail['discount_price'] = str(Decimal(dishes_detail['price']) -
                                                  Decimal(dishes_detail['discount']))
        else:
            dishes_detail['discount_price'] = dishes_detail['price']
        return dishes_detail

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

        perfect_hot_list = []
        for detail in hot_list:
            perfect_detail = self.get_perfect_dishes_detail(detail)
            perfect_hot_list.append(perfect_detail)
        return perfect_hot_list

    def get_dishes_detail(self, dishes_id):
        key = self.get_dishes_id_key(dishes_id)
        detail = self.handle.get(key)
        if not detail:
            detail = Dishes.get_dishes_detail_dict_with_user_info(**{'pk': dishes_id})
            if isinstance(detail, Exception):
                return detail
            self.set_data_to_cache(key, detail)
        return self.get_perfect_dishes_detail(detail)

