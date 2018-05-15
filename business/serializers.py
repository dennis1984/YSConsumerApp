# -*- coding:utf8 -*-
from rest_framework import serializers
from Business_App.bz_dishes.models import Dishes, City
from Business_App.bz_users.models import FoodCourt,BusinessUser
from horizon.serializers import BaseListSerializer
from django.conf import settings
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseDishesDetailSerializer)
import os

##

class DishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = '__all__'


class DishesDetailSerializer(BaseDishesDetailSerializer):
    is_collected = serializers.NullBooleanField(required=False)
    tag = serializers.CharField(allow_null=True, allow_blank=True)
    sort_orders = serializers.IntegerField(allow_null=True)



class BusinessUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUser
        fields = ('id', 'phone', 'business_name','business_summary', 'food_court_id',
                    'brand', 'manager', 'chinese_people_id', 'stalls_number',
                    'is_active', 'date_joined', 'last_login', 'head_picture',)

class UserDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    phone = serializers.CharField(max_length=20)
    business_name = serializers.CharField(max_length=100)
    food_court_id = serializers.IntegerField()
    brand = serializers.CharField(allow_blank=True, allow_null=True)
    manager = serializers.CharField(max_length=20, allow_null=True, allow_blank=True)
    chinese_people_id = serializers.CharField(max_length=25, allow_blank=True,
                                              allow_null=True)
    stalls_number = serializers.CharField(max_length=20, allow_blank=True,
                                          allow_null=True)

    business_summary = serializers.CharField(allow_blank=True, allow_null=True)
    last_login = serializers.DateTimeField()
    date_joined = serializers.DateTimeField()
    is_active = serializers.BooleanField()

    head_picture = serializers.ImageField()
    food_court_name = serializers.CharField(max_length=200, required=False)
    city = serializers.CharField(max_length=100, required=False)
    district = serializers.CharField(max_length=100, required=False)
    mall = serializers.CharField(max_length=200, required=False)

    @property
    def data(self):
        _data = super(UserDetailSerializer, self).data
        if _data.get('id', None):
            base_dir = _data['head_picture'].split('static', 1)[1]
            if base_dir.startswith(os.path.sep):
                base_dir = base_dir[1:]
            _data['head_picture_url'] = os.path.join(settings.WEB_URL_FIX,
                                                     'static',
                                                     base_dir)
            _data.pop('head_picture')
        return _data

class BusinessUserListSerializer(BaseListSerializer):
    child = BusinessUserSerializer()


class BusinessDishesListSerializer(BaseListSerializer):
    child = DishesDetailSerializer()


