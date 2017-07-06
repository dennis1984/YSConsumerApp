# -*- coding:utf8 -*-
from collect.models import Collect
from horizon.decorators import has_permission_to_update
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseListSerializer)
from Business_App.bz_dishes.models import Dishes
from rest_framework import serializers

from horizon.main import make_random_number_of_string
from horizon.decorators import has_permission_to_update

import os


class CollectSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            request = kwargs['request']
            data['user_id'] = request.user.id
            kwargs.pop('request')
            super(CollectSerializer, self).__init__(data=data, **kwargs)
        else:
            super(CollectSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Collect
        fields = '__all__'

    def save(self, **kwargs):
        try:
            return super(CollectSerializer, self).save(**kwargs)
        except Exception as e:
            return e

    @has_permission_to_update
    def delete(self, request, instance):
        validated_data = {'status': 2,
                          'dishes_id': '%s%08d' % (instance.dishes_id,
                                                   int(make_random_number_of_string(5)))}
        try:
            return super(CollectSerializer, self).update(instance, validated_data)
        except Exception as e:
            return e


class DishesDetailSerializer(BaseSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    subtitle = serializers.CharField(max_length=200, required=False,
                                     allow_blank=True, allow_null=True)
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


class CollectListSerializer(BaseListSerializer):
    child = DishesDetailSerializer()
