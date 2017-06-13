#-*- coding:utf8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password
from oauth2_provider.models import AccessToken
from horizon.models import model_to_dict
from horizon.main import minutes_15_plus
import datetime


class ConsumerUserManager(BaseUserManager):
    def create_user(self, username, password, **kwargs):
        """
        创建消费者用户，
        参数包括：username （手机号）
                 password （长度必须不小于6位）
        """
        if not username:
            raise ValueError('Username cannot be null!')
        if len(password) < 6:
            raise ValueError('Password length must not less then 6!')

        user = self.model(phone=username)
        user.set_password(password)
        user.save(using=self._db)
        return user


class ConsumerUser(AbstractBaseUser):
    phone = models.CharField(u'手机号', max_length=20, unique=True, db_index=True)
    nickname = models.CharField(u'昵称', max_length=100, unique=True, null=True)

    # 性别，0：未设定，1：男，2：女
    gender = models.IntegerField(u'性别', default=0)
    birthday = models.DateField(u'生日', null=True)
    region = models.CharField(u'所在地区', max_length=64, null=True)
    head_picture = models.ImageField(u'头像',
                                     upload_to='static/picture/consume/head_picture/',
                                     default='static/picture/consume/head_picture/noImage.png')

    # 注册渠道：客户端：YS，微信第三方：WX，QQ第三方：QQ，淘宝：TB
    #          新浪微博：SINA_WB
    channel = models.CharField(u'注册渠道', max_length=20, default='YS')
    is_active = models.BooleanField(default=True)
    # is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(u'创建时间', default=now)
    updated = models.DateTimeField(u'最后更新时间', auto_now=True)

    objects = ConsumerUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['channel']

    class Meta:
        db_table = 'ys_auth_consume_user'
        # unique_together = ('nickname', 'food_court_id')

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    @classmethod
    def get_object(cls, **kwargs):
        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist as e:
            return Exception(e)

    @classmethod
    def get_user_detail(cls, request):
        """
        return: ConsumerUser instance
        """
        try:
            return cls.objects.get(pk=request.user.id)
        except Exception as e:
            return e

    @classmethod
    def get_objects_list(cls, request, **kwargs):
        """
        获取用户列表
        权限控制：只有管理员可以访问这些数据
        """
        if not request.user.is_admin:
            return Exception('Permission denied, Cannot access the method')

        _kwargs = {}
        if 'start_created' in kwargs:
            _kwargs['created__gte'] = kwargs['start_created']
        if 'end_created' in kwargs:
            _kwargs['created__lte'] = kwargs['end_created']
        _kwargs['is_admin'] = False
        try:
            return cls.objects.filter(**_kwargs)
        except Exception as e:
            return e


def make_token_expire(request):
    """
    置token过期
    """
    header = request.META
    token = header['HTTP_AUTHORIZATION'].split()[1]
    try:
        _instance = AccessToken.objects.get(token=token)
        _instance.expires = now()
        _instance.save()
    except:
        pass
    return True


class IdentifyingCode(models.Model):
    phone = models.CharField(u'手机号', max_length=20, db_index=True)
    identifying_code = models.CharField(u'手机验证码', max_length=6)
    expires = models.DateTimeField(u'过期时间', default=minutes_15_plus)

    class Meta:
        db_table = 'ys_identifying_code'
        ordering = ['-expires']

    def __unicode__(self):
        return self.phone

    @classmethod
    def get_object_by_phone(cls, phone):
        instances = cls.objects.filter(**{'phone': phone, 'expires__gt': now()})
        if instances:
            return instances[0]
        else:
            return None

