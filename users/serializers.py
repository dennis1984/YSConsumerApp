# -*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from users.models import ConsumerUser, IdentifyingCode
from horizon.serializers import BaseListSerializer, timezoneStringTostring
from django.conf import settings
from horizon.models import model_to_dict
from horizon import main
from horizon.decorators import has_permission_to_update
import urllib
import os
import json
import re
import copy


class WXUserSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            _data = copy.deepcopy(data)
            _data['gender'] = _data.pop('sex')
            _data['out_open_id'] = _data.pop('openid')
            # data['head_picture'] = data.pop('headimgurl')
            # _data['phone'] = 'WX%s' % main.make_random_char_and_number_of_string(18)
            self.make_correct_params(_data)
            super(WXUserSerializer, self).__init__(data=_data, **kwargs)
        else:
            super(WXUserSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = ConsumerUser
        fields = ('phone', 'out_open_id', 'nickname', 'gender',
                  'province', 'city', 'head_picture')

    def is_valid(self, raise_exception=False):
        result = super(WXUserSerializer, self).is_valid(raise_exception)
        if not result:
            if self.errors.keys() == ['head_picture']:
                return True
            return False
        return True

    def save(self, **kwargs):
        kwargs['channel'] = 'WX'
        kwargs['password'] = make_password(self.validated_data['out_open_id'])
        kwargs['head_picture'] = self.initial_data['headimgurl']
        return super(WXUserSerializer, self).save(**kwargs)

    def make_correct_params(self, source_dict):
        """
        解决微信授权登录后返回用户信息乱码的问题
        """
        zh_cn_list = ['nickname', 'city', 'province', 'country']
        compile_str = '\\u00[0-9a-z]{2}'
        re_com = re.compile(compile_str)
        for key in source_dict.keys():
            if key in zh_cn_list:
                utf8_list = re_com.findall(json.dumps(source_dict[key]))
                unicode_list = []
                for ch_item in utf8_list:
                    exec('unicode_list.append("\\x%s")' % ch_item.split('u00')[1])
                key_tmp_list = [json.dumps(source_dict[key])[1:-1]]
                for item2 in utf8_list:
                    tmp2 = key_tmp_list[-1].split('\\%s' % item2, 1)
                    key_tmp_list.pop(-1)
                    key_tmp_list.extend(tmp2)

                for index in range(len(key_tmp_list)):
                    if not key_tmp_list[index]:
                        if index < len(unicode_list):
                            key_tmp_list[index] = unicode_list[index]
                source_dict[key] = ''.join(key_tmp_list).decode('utf8')
        return source_dict


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

    def binding_phone_to_user(self, request, instance, validated_data):
        _validated_data = {'phone': validated_data['username']}
        return super(UserSerializer, self).update(instance, _validated_data)


class UserInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumerUser
        fields = ('id', 'phone', 'nickname', 'head_picture',)


class UserDetailSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    phone = serializers.CharField(max_length=20, allow_blank=True,
                                  allow_null=True)
    nickname = serializers.CharField(max_length=100, required=False)
    gender = serializers.IntegerField(default=0)
    birthday = serializers.DateField(required=False)
    region = serializers.CharField(required=False)
    channel = serializers.CharField(default='YS')
    province = serializers.CharField(max_length=16)
    city = serializers.CharField(max_length=32)
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
            _data['member_id'] = 'NO.%06d' % _data['pk']
            _data['last_login'] = timezoneStringTostring(_data['last_login'])
            head_picture = _data.pop('head_picture')
            if head_picture.startswith('http'):
                _data['head_picture_url'] = urllib.unquote(head_picture)
            else:
                _data['head_picture_url'] = os.path.join(settings.WEB_URL_FIX,
                                                         head_picture)
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

