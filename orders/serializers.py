# -*- coding:utf8 -*-
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from orders.models import (PayOrders,
                           ConsumeOrders,
                           ConfirmConsume)
from horizon.serializers import (BaseListSerializer,
                                 BaseModelSerializer,
                                 BaseSerializer)
from django.conf import settings
from horizon.models import model_to_dict
from horizon.decorators import has_permission_to_update
import os


class PayOrdersSerializer(BaseModelSerializer):
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
    orders_type = serializers.IntegerField()
    is_expired = serializers.BooleanField()
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    extend = serializers.CharField(allow_blank=True)


class ConsumeOrdersSerializer(BaseModelSerializer):
    class Meta:
        model = ConsumeOrders
        fields = '__all__'

    def set_commented(self, instance):
        validated_data = {'is_commented': 1}
        try:
            return self.update(instance, validated_data)
        except Exception as e:
            return e


class ConsumeOrdersResponseSerializer(BaseSerializer):
    id = serializers.IntegerField()
    orders_id = serializers.CharField(max_length=32)
    user_id = serializers.IntegerField()
    food_court_id = serializers.IntegerField()
    food_court_name = serializers.CharField(max_length=200)
    business_name = serializers.CharField(max_length=200)
    business_id = serializers.IntegerField()

    dishes_ids = serializers.ListField()

    total_amount = serializers.CharField(max_length=16)
    member_discount = serializers.CharField(max_length=16)
    other_discount = serializers.CharField(max_length=16)
    payable = serializers.CharField(max_length=16)

    payment_status = serializers.IntegerField()
    payment_mode = serializers.IntegerField()
    orders_type = serializers.IntegerField()
    master_orders_id = serializers.CharField(max_length=32)
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    extend = serializers.CharField(allow_blank=True)


class OrdersDetailSerializer(object):
    def __init__(self, instance=None, data=None, **kwargs):
        self.instance = None
        if data:
            if 'master_orders_id' in data:
                self.instance = ConsumeOrdersResponseSerializer(data=data, **kwargs)
            else:
                self.instance = PayOrdersResponseSerializer(data=data, **kwargs)
        else:
            if hasattr(instance, 'master_orders_id'):
                self.instance = ConsumeOrdersResponseSerializer(instance, **kwargs)
            else:
                self.instance = PayOrdersResponseSerializer(instance, **kwargs)


class OrdersDetailForListSerializer(BaseSerializer):
    id = serializers.IntegerField()
    orders_id = serializers.CharField(max_length=32)
    user_id = serializers.IntegerField()
    food_court_id = serializers.IntegerField()
    food_court_name = serializers.CharField(max_length=200)
    business_name = serializers.CharField(max_length=200, required=False,
                                          allow_blank=True, allow_null=True)
    business_id = serializers.IntegerField(required=False, allow_null=True)

    dishes_ids = serializers.ListField()

    total_amount = serializers.CharField(max_length=16)
    member_discount = serializers.CharField(max_length=16)
    other_discount = serializers.CharField(max_length=16)
    payable = serializers.CharField(max_length=16)

    payment_status = serializers.IntegerField()
    payment_mode = serializers.IntegerField()
    orders_type = serializers.IntegerField()

    # 交易类型：'pay'：支付订单  'consume'：核销订单
    trade_type = serializers.CharField()

    master_orders_id = serializers.CharField(max_length=32, required=False,
                                             allow_null=True, allow_blank=True)
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    expires = serializers.DateTimeField()

    # 是否过期
    is_expired = serializers.NullBooleanField(required=False)
    # 是否评价过
    is_commented = serializers.IntegerField(required=False, allow_null=True)

    extend = serializers.CharField(allow_blank=True)


class OrdersListSerializer(BaseListSerializer):
    child = OrdersDetailForListSerializer()


class ConfirmConsumeSerializer(BaseModelSerializer):
    class Meta:
        model = ConfirmConsume
        fields = '__all__'
