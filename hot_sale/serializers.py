# -*- coding:utf8 -*-
from rest_framework import serializers
from Business_App.bz_dishes.models import Dishes, City
from Business_App.bz_users.models import FoodCourt
from horizon.serializers import BaseListSerializer
from django.conf import settings
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseDishesDetailSerializer)
import os


class DishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = '__all__'


class DishesDetailSerializer(BaseDishesDetailSerializer):
    is_collected = serializers.NullBooleanField(required=False)
    tag = serializers.CharField(allow_null=True, allow_blank=True)
    sort_orders = serializers.IntegerField(allow_null=True)


class HotSaleSerializer(BaseListSerializer):
    child = DishesDetailSerializer()


class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()
