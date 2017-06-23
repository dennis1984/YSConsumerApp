# -*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from orders.models import PayOrders, ConsumeOrders
from horizon.serializers import BaseListSerializer, timezoneStringTostring
from django.conf import settings
from horizon.models import model_to_dict
from horizon.decorators import has_permission_to_update
from horizon.serializers import BaseSerializer
import os


class PayOrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayOrders
        fields = '__all__'
        # fields = ('id', 'phone', 'business_name', 'head_picture',
        #           'food_court_id')

    @has_permission_to_update
    def update_userinfo(self, request, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super(PayOrdersSerializer, self).update(instance, validated_data)


class PayOrdersResponseSerializer(BaseSerializer):
    id = serializers.IntegerField()
    orders_id = serializers.CharField(max_length=32)
    user_id = serializers.IntegerField()
    food_court_id = serializers.IntegerField()
    food_court_name = serializers.CharField(max_length=200)

    dishes_ids = serializers.ListField()

    total_amount = serializers.CharField(max_length=16)
    member_discount = serializers.CharField(max_length=16)
    other_discount = serializers.CharField(max_length=16)
    payable = serializers.CharField(max_length=16)
    payment_status = serializers.IntegerField()
    payment_mode = serializers.IntegerField()
    orders_status = serializers.IntegerField()
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    extend = serializers.CharField(allow_blank=True)


#
# class UserInstanceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ConsumerUser
#         fields = ('id', 'phone', 'nickname', 'head_picture',)
#
#
# class UserDetailSerializer(serializers.Serializer):
#     pk = serializers.IntegerField()
#     phone = serializers.CharField(max_length=20)
#     nickname = serializers.CharField(max_length=100, required=False)
#     gender = serializers.IntegerField(default=0)
#     birthday = serializers.DateField(required=False)
#     region = serializers.CharField(required=False)
#     channel = serializers.CharField(default='YS')
#     last_login = serializers.DateTimeField()
#
#     head_picture = serializers.ImageField()
#
#
#     # food_court_name = serializers.CharField(max_length=200, required=False)
#     # city = serializers.CharField(max_length=100, required=False)
#     # district = serializers.CharField(max_length=100, required=False)
#     # mall = serializers.CharField(max_length=200, required=False)
#
#     @property
#     def data(self):
#         _data = super(UserDetailSerializer, self).data
#         if _data.get('pk', None):
#             _data['last_login'] = timezoneStringTostring(_data['last_login'])
#             _data['head_picture_url'] = os.path.join(settings.WEB_URL_FIX, _data['head_picture'])
#         return _data
#
#
# class UserListSerializer(BaseListSerializer):
#     child = UserDetailSerializer()
#
#
# class GroupSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Group
#         fields = ('url', 'name')
#
#
# class IdentifyingCodeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = IdentifyingCode
#         fields = '__all__'

