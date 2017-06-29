#-*- coding:utf8 -*-
from rest_framework import serializers
from shopping_cart.models import ShoppingCart
from Business_App.bz_dishes.models import Dishes
from horizon.serializers import BaseListSerializer, timezoneStringTostring
from django.conf import settings
from horizon.serializers import BaseSerializer
from horizon.decorators import has_permission_to_update
import os


class ShoppingCartSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        if '_request' in kwargs:
            request = kwargs['_request']
            if 'data' not in kwargs:
                data = request.data.copy()
            else:
                data = kwargs['data']
            data['user_id'] = request.user.id
            super(ShoppingCartSerializer, self).__init__(data=data)
        else:
            super(ShoppingCartSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    @has_permission_to_update
    def update_instance_count(self, request, instance, validated_data):
        instance_count = count = validated_data['count']
        if 'method' in validated_data:
            if validated_data['method'] == 'sub':
                count = -count
            instance_count = instance.count + count
        if instance_count < 1:
            raise ValueError('Instance count must be more than 0')
        kwargs = {'count': instance_count}
        return super(ShoppingCartSerializer, self).update(instance, kwargs)

    @has_permission_to_update
    def delete_instance(self, request, instance):
        kwargs = {'status': 2}
        return super(ShoppingCartSerializer, self).update(instance, kwargs)


class ShoppingCartDetailSerializer(BaseSerializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    dishes_id = serializers.IntegerField()
    count = serializers.IntegerField()
    updated = serializers.DateTimeField()
    dishes_detail = serializers.DictField()


class ShoppingCartListSerializer(BaseListSerializer):
    child = ShoppingCartDetailSerializer()
