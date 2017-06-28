# -*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from Business_App.bz_dishes.models import Dishes
from Business_App.bz_users.models import FoodCourt
from horizon.serializers import BaseListSerializer, timezoneStringTostring
from django.conf import settings
from horizon.serializers import BaseSerializer
from horizon.models import model_to_dict
from horizon.decorators import has_permission_to_update
import os
class DishesSerializer(serializers.ModelSerializer):
    # def __init__(self, *args, **kwargs):
    #     if '_request' in kwargs:
    #         request = kwargs['_request']
    #         data = request.data.copy()
    #         #data['user_id'] = request.user.id
    #         # data['food_court_id'] = request.food_court_id
    #         # data['is_recommend'] = request.is_recommend
    #
    #         # 处理管理后台上传图片图片名字没有后缀的问题
    #         # if 'image' in data:
    #         #     image_names = data['image'].name.split('.')
    #         #     if len(image_names) == 1:
    #         #         data['image'].name = '%s.png' % image_names[0]
    #         super(DishesSerializer, self).__init__(data=data)
    #     else:
    #         super(DishesSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Dishes
        # fields = ('dishes_id', 'title', 'subtitle', 'description',
        #           'price', 'image_url', 'user_id', 'extend')
        fields = '__all__'
class DishesDetailSerializer(BaseSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    business_name = serializers.CharField()
    price = serializers.CharField()
    image_url = serializers.CharField()
    # updated = serializers.DateTimeField()
    # dishes_detail = serializers.DictField()

class HotSaleSerializer(BaseListSerializer):

    child = DishesDetailSerializer()

class FoodCourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodCourt
        fields = '__all__'


class FoodCourtListSerializer(BaseListSerializer):
    child = FoodCourtSerializer()


