# -*- coding:utf8 -*-
from rest_framework import serializers
from rest_framework import fields as Fields
from django.core.paginator import Paginator
from django.conf import settings
from django.db import models
from horizon.main import timezoneStringTostring
from horizon.models import model_to_dict
import os
import datetime


class BaseListSerializer(serializers.ListSerializer):
    def list_data(self, page_size=settings.PAGE_SIZE, page_index=1, **kwargs):
        """
        函数功能：分页
        返回数据格式为：{'count': 当前返回的数据量,
                       'all_count': 总数据量,
                       'has_next': 是否有下一页,
                       'data': [{
                                  model数据
                                },...]
                       }
        """
        # page size不能超过默认最大值，如果超过，则按page size默认最大值返回数据
        if page_size > settings.MAX_PAGE_SIZE:
            page_size = settings.MAX_PAGE_SIZE
        serializer = self.perfect_result()
        paginator = Paginator(serializer, page_size)
        try:
            page = paginator.page(page_index)
        except Exception as e:
            return e

        has_next = True
        if len(page.object_list) < page_size:
            has_next = False
        elif page_size * page_index >= len(serializer):
            has_next = False
        results = {'count': len(page.object_list),
                   'all_count': len(serializer),
                   'has_next': has_next,
                   'data': page.object_list}
        return results

    def perfect_result(self):
        dict_format = {}
        if hasattr(self, 'initial_data'):
            if len(self.initial_data) > 0:
                dict_format = self.initial_data[0]
        else:
            if len(self.instance) > 0:
                dict_format = model_to_dict(self.instance[0])
        ordered_dict = self.data
        for item in ordered_dict:
            for key in item.keys():
                if isinstance(dict_format[key], datetime.datetime):
                    item[key] = timezoneStringTostring(item[key])
                if isinstance(dict_format[key], models.fields.files.ImageFieldFile):
                    item['%s_url' % key] = os.path.join(settings.WEB_URL_FIX, item[key])
        return ordered_dict


class BaseSerializer(serializers.Serializer):
    @property
    def data(self):
        _data = super(BaseSerializer, self).data
        return perfect_result(self, _data)


class BaseModelSerializer(serializers.ModelSerializer):
    @property
    def data(self):
        _data = super(BaseModelSerializer, self).data
        return perfect_result(self, _data)


def perfect_result(self, _data):
    _fields = self.get_fields()
    for key in _data:
        if isinstance(_fields[key], Fields.DateTimeField):
            _data[key] = timezoneStringTostring(_data[key])
        if isinstance(_fields[key], Fields.ImageField):
            _data['%s_url' % key] = os.path.join(settings.WEB_URL_FIX, _data[key])
    return _data


class BaseDishesDetailSerializer(BaseSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    subtitle = serializers.CharField(max_length=200, required=False,
                                     allow_blank=True, allow_null=True)
    description = serializers.CharField(max_length=500, required=False,
                                        allow_null=True, allow_blank=True)
    # 默认：10，小份：11，中份：12，大份：13，自定义：20
    size = serializers.IntegerField()
    size_detail = serializers.CharField(max_length=30, required=False,
                                        allow_null=True, allow_blank=True)
    price = serializers.CharField(max_length=50)
    image_url = serializers.CharField(max_length=200)
    user_id = serializers.IntegerField()

    updated = serializers.DateTimeField()
    business_id = serializers.IntegerField()
    business_name = serializers.CharField(max_length=100)
    food_court_id = serializers.IntegerField()
    food_court_name = serializers.CharField(max_length=200)
