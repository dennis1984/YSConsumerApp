# -*- coding:utf8 -*-
from rest_framework import serializers
from users.wx_auth.models import WXRandomString, WXAccessToken
from django.utils.timezone import now
from horizon.main import make_time_delta
from oauth2_provider.models import (AccessToken as Oauth2_AccessToken,
                                    RefreshToken as Oauth2_RefreshToken)
import os
import hashlib


class RandomStringSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            data['random_str'] = hashlib.md5(data['random_str']).hexdigest()
            super(RandomStringSerializer, self).__init__(data=data, **kwargs)
        else:
            super(RandomStringSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = WXRandomString
        fields = '__all__'


class AccessTokenSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            seconds_plus = data.pop('expires_in')
            data['expires'] = make_time_delta(seconds=seconds_plus)
            super(AccessTokenSerializer, self).__init__(data=data, **kwargs)
        else:
            super(AccessTokenSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = WXAccessToken
        fields = '__all__'

    def save(self, **kwargs):
        # seconds_plus = kwargs.pop('expires_in')
        # kwargs['expires'] = make_time_delta(seconds=seconds_plus)
        return super(AccessTokenSerializer, self).save(**kwargs)


class Oauth2AccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oauth2_AccessToken
        fields = '__all__'


class Oauth2RefreshTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oauth2_RefreshToken
        fields = '__all__'


# class Oauth2AccessTokenSerializer(serializers.Serializer):
#     token = serializers.CharField(max_length=255)
#     expires = serializers.DateTimeField()
#     scope = serializers.CharField(max_length=255)
#     application_id = serializers.IntegerField()
#     user_id = serializers.IntegerField()
#
#
# class Oauth2RefreshTokenSerializer(serializers.Serializer):
#     token = serializers.CharField(max_length=255)
#     access_token_id = serializers.IntegerField()
#     application_id = serializers.IntegerField()
#     user_id = serializers.IntegerField()
