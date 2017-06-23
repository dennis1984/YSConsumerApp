#-*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from users.models import ConsumerUser, IdentifyingCode
from horizon.serializers import BaseListSerializer, timezoneStringTostring
from django.conf import settings
from horizon.models import model_to_dict
from horizon.decorators import has_permission_to_update
import os


class WXUserSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            data['gender'] = data.pop('sex')
            data['out_open_id'] = data.pop('openid')
            # data['head_picture'] = data.pop('headimgurl')
            data['phone'] = 'WX_USER'
            super(WXUserSerializer, self).__init__(data=data, **kwargs)
        else:
            super(WXUserSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = ConsumerUser
        fields = ('out_open_id', 'nickname', 'gender',
                  'province', 'city', 'head_picture')

    def save(self, **kwargs):
        kwargs['channel'] = 'WX'
        kwargs['password'] = make_password(self.validated_data['out_open_id'])
        return super(WXUserSerializer, self).save(**kwargs)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumerUser
        fields = '__all__'
        # fields = ('id', 'phone', 'business_name', 'head_picture',
        #           'food_court_id')

    @has_permission_to_update
    def update_password(self, request, instance, validated_data):
        password = validated_data.get('password', None)
        if password is None:
            raise ValueError('Password is cannot be empty.')
        validated_data['password'] = make_password(password)
        return super(UserSerializer, self).update(instance, validated_data)

    @has_permission_to_update
    def update_userinfo(self, request, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super(UserSerializer, self).update(instance, validated_data)


class UserInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumerUser
        fields = ('id', 'phone', 'nickname', 'head_picture',)


class UserDetailSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    phone = serializers.CharField(max_length=20)
    nickname = serializers.CharField(max_length=100, required=False)
    gender = serializers.IntegerField(default=0)
    birthday = serializers.DateField(required=False)
    region = serializers.CharField(required=False)
    channel = serializers.CharField(default='YS')
    last_login = serializers.DateTimeField()

    head_picture = serializers.ImageField()


    # food_court_name = serializers.CharField(max_length=200, required=False)
    # city = serializers.CharField(max_length=100, required=False)
    # district = serializers.CharField(max_length=100, required=False)
    # mall = serializers.CharField(max_length=200, required=False)

    @property
    def data(self):
        _data = super(UserDetailSerializer, self).data
        if _data.get('pk', None):
            _data['last_login'] = timezoneStringTostring(_data['last_login'])
            _data['head_picture_url'] = os.path.join(settings.WEB_URL_FIX, _data['head_picture'])
        return _data


class UserListSerializer(BaseListSerializer):
    child = UserDetailSerializer()


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class IdentifyingCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentifyingCode
        fields = '__all__'

