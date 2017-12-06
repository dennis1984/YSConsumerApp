# -*- coding:utf8 -*-
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from orders.models import (PayOrders,
                           ConsumeOrders,
                           ConfirmConsume,)
from horizon.serializers import (BaseListSerializer,
                                 BaseModelSerializer,
                                 BaseSerializer,
                                 BaseDishesDetailSerializer)
from Business_App.bz_dishes.models import Dishes
from Business_App.bz_orders.models import YinshiPayCode
from django.conf import settings
from horizon.models import model_to_dict
from horizon.decorators import has_permission_to_update
import os


class PayOrdersSerializer(BaseModelSerializer):
    class Meta:
        model = PayOrders
        fields = '__all__'

    def save(self, **kwargs):
        # 将主订单ID写入YinshiPayCode
        if kwargs.get('gateway') == 'yinshi_pay':
            random_code = kwargs['random_code']
            ys_pay_instance = YinshiPayCode.get_object(code=random_code)
            if isinstance(ys_pay_instance, Exception):
                raise ys_pay_instance
            if ys_pay_instance.pay_orders_id:
                raise Exception('Can not perform this action.')
            ys_pay_instance.pay_orders_id = self.validated_data['orders_id']
            ys_pay_instance.save()
        return super(PayOrdersSerializer, self).save()


class PayOrdersResponseSerializer(BaseSerializer):
    id = serializers.IntegerField()
    orders_id = serializers.CharField(max_length=32)
    user_id = serializers.IntegerField()
    food_court_id = serializers.IntegerField()
    food_court_name = serializers.CharField(max_length=200)

    dishes_ids = serializers.ListField()

    total_amount = serializers.CharField(max_length=16)
    member_discount = serializers.CharField(max_length=16)
    online_discount = serializers.CharField(max_length=16)
    other_discount = serializers.CharField(max_length=16)
    coupons_discount = serializers.CharField(max_length=16)
    payable = serializers.CharField(max_length=16)
    payment_status = serializers.IntegerField()
    payment_mode = serializers.IntegerField()
    orders_type = serializers.IntegerField()
    is_expired = serializers.BooleanField()
    notes = serializers.CharField(allow_null=True, allow_blank=True)

    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    extend = serializers.CharField(allow_blank=True)


class PayOrdersConfirmSerializer(PayOrdersResponseSerializer):
    id = serializers.IntegerField(required=False)
    orders_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    payment_status = serializers.IntegerField(required=False, allow_null=True)
    payment_mode = serializers.IntegerField(required=False, allow_null=True)
    is_expired = serializers.NullBooleanField(required=False)

    request_data = serializers.DictField()
    notes = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    created = serializers.DateTimeField(required=False, allow_null=True)
    updated = serializers.DateTimeField(required=False, allow_null=True)
    expires = serializers.DateTimeField(required=False, allow_null=True)
    extend = serializers.CharField(required=False, allow_null=True, allow_blank=True)


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
    stalls_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    dishes_ids = serializers.ListField()

    total_amount = serializers.CharField(max_length=16)
    member_discount = serializers.CharField(max_length=16)
    online_discount = serializers.CharField(max_length=16)
    other_discount = serializers.CharField(max_length=16)
    coupons_discount = serializers.CharField(max_length=16)
    payable = serializers.CharField(max_length=16)

    payment_status = serializers.IntegerField()
    payment_mode = serializers.IntegerField()
    orders_type = serializers.IntegerField()
    master_orders_id = serializers.CharField(max_length=32)
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    # 是否评价过
    is_commented = serializers.IntegerField(allow_null=True)
    notes = serializers.CharField(allow_null=True, allow_blank=True)
    # 核销时段：例如：17:30~20:30
    consumer_time_slot = serializers.CharField(allow_null=True, allow_blank=True)

    extend = serializers.CharField(allow_blank=True)


class ConsumeOrdersListSerializer(BaseListSerializer):
    child = ConsumeOrdersResponseSerializer()


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
    stalls_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    dishes_ids = serializers.ListField()

    total_amount = serializers.CharField(max_length=16)
    member_discount = serializers.CharField(max_length=16)
    online_discount = serializers.CharField(max_length=16)
    other_discount = serializers.CharField(max_length=16)
    coupons_discount = serializers.CharField(max_length=16)
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
    notes = serializers.CharField(allow_null=True, allow_blank=True)

    extend = serializers.CharField(allow_blank=True)


class OrdersListSerializer(BaseListSerializer):
    child = OrdersDetailForListSerializer()


class ConfirmConsumeSerializer(BaseModelSerializer):
    class Meta:
        model = ConfirmConsume
        fields = '__all__'


class YSPayDishesSerializer(BaseDishesDetailSerializer):
    count = serializers.IntegerField()


class YSPayDishesListSerializer(BaseListSerializer):
    child = YSPayDishesSerializer()
