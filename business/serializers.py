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


class BusinessUserListSerializer(BaseListSerializer):
    child = BusinessUserSerializer()


class BusinessDishesListSerializer(BaseListSerializer):
    child = DishesDetailSerializer()


