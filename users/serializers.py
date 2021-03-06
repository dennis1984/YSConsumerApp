# -*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from users.models import ConsumerUser, IdentifyingCode
from django.conf import settings

from horizon.models import model_to_dict
from horizon import main
from horizon.decorators import has_permission_to_update
from horizon.serializers import (BaseListSerializer,
                                 BaseModelSerializer,
                                 BaseSerializer,
                                 timezoneStringTostring)
from Business_App.bz_users.models import AdvertPicture
from Admin_App.ad_coupons.models import CouponsSendRecord

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
                try:
                    source_dict[key] = ''.join(key_tmp_list).decode('utf8')
                except:
                    source_dict[key] = ''
        return source_dict


class UserSerializer(BaseModelSerializer):
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
        instance = super(UserSerializer, self).update(instance, _validated_data)

        # 同步手机号到优惠券发送记录
        records = CouponsSendRecord.filter_objects(user_id=instance.id)
        for record in records:
            record.phone = _validated_data['phone']
            try:
                record.save()
            except:
                return

        return instance


class UserInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumerUser
        fields = ('id', 'phone', 'nickname', 'head_picture',)


class UserDetailSerializer(BaseSerializer):
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

    @property
    def data(self):
        _data = super(UserDetailSerializer, self).data
        if _data.get('pk', None):
            _data['member_id'] = 'NO.%06d' % _data['pk']
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


class AdvertPictureSerializer(BaseModelSerializer):
    class Meta:
        model = AdvertPicture
        fields = '__all__'


class AdvertPictureListSerializer(BaseListSerializer):
    child = AdvertPictureSerializer()
