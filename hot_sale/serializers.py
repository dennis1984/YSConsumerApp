# -*- coding:utf8 -*-
from rest_framework import serializers
from Business_App.bz_dishes.models import Dishes
from Business_App.bz_users.models import FoodCourt
from horizon.serializers import BaseListSerializer
from django.conf import settings
from horizon.serializers import (BaseSerializer,
                                 BaseDishesDetailSerializer)
import os


class DishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dishes
        fields = '__all__'


# class DishesDetailSerializer(BaseSerializer):
#     id = serializers.IntegerField()
#     title = serializers.CharField()
#     business_name = serializers.CharField()
#     price = serializers.CharField()
#     image_url = serializers.CharField()

class DishesDetailSerializer(BaseDishesDetailSerializer):
    is_collected = serializers.NullBooleanField(required=False)


class HotSaleSerializer(BaseListSerializer):
    child = DishesDetailSerializer()


class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()
