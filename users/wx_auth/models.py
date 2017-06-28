# -*- coding:utf8 -*-
from django.db import models
from django.utils.timezone import now
from horizon.main import minutes_15_plus
from oauth2_provider.models import (Application as Oauth2_Application,
                                    AccessToken as Oauth2_AccessToken,
                                    RefreshToken as Oauth2_RefreshToken)
import datetime
from hashlib import md5


class WXAccessToken(models.Model):
    access_token = models.CharField(u'微信授权访问用户的token', max_length=256, unique=True)
    refresh_token = models.CharField(u'刷新access token的token', max_length=256, unique=True)
    openid = models.CharField(u'微信用户唯一标识', max_length=64, db_index=True)
    scope = models.CharField(u'用户授权的作用域', max_length=64)
    unionid = models.CharField(u'unionid', max_length=32)
    state = models.CharField(u'获取微信code的随机数', max_length=128)
    expires = models.DateTimeField(u'过期时间')

    class Meta:
        db_table = 'ys_wxauth_accesstoken'
        ordering = ['-expires']

    def __unicode__(self):
        return self.openid

    @classmethod
    def get_object_by_openid(cls, openid):
        instances = cls.objects.filter(**{'openid': openid, 'expires__gt': now()})
        if instances:
            return instances[0]
        else:
            return None


class WXRandomString(models.Model):
    random_str = models.CharField(u'随机字符串', max_length=32, db_index=True)
    status = models.IntegerField(u'随机字符串状态', default=0)     # 0：未使用，1：已使用
    expires = models.DateTimeField(u'过期时间', default=minutes_15_plus)

    class Meta:
        db_table = 'ys_wxauth_randomstring'
        ordering = ['-expires']

    def __unicode__(self):
        return self.random_str

    @classmethod
    def get_object_by_random_str(cls, random_str):
        random_str = md5(random_str).hexdigest()
        instances = cls.objects.filter(**{'random_str': random_str,
                                          'expires__gt': now(),
                                          'status': 0})
        if instances:
            return instances[0]
        else:
            return None
