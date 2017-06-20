#-*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from shopping_cart.models import ShoppingCart
from horizon.serializers import BaseListSerializer, timezoneStringTostring
from django.conf import settings
from horizon.models import model_to_dict
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
        if 'method' not in validated_data:
            raise KeyError('Method does not existed in validated_data')
        count = validated_data['count']
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


class ShoppingCartDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    dishes_id = serializers.IntegerField()
    count = serializers.IntegerField()
    updated = serializers.DateTimeField()
    dishes_detail = serializers.DictField()

    @property
    def data(self):
        _data = super(ShoppingCartDetailSerializer, self).data
        if _data.get('id', None):
            _data['updated'] = timezoneStringTostring(_data['updated'])
        return _data


class ShoppingCartListSerializer(BaseListSerializer):
    child = ShoppingCartDetailSerializer()
