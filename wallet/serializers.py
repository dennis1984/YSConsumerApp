# -*- coding:utf8 -*-
from django.contrib.auth.hashers import make_password
from wallet.models import Wallet, WalletTradeDetail
from horizon.decorators import has_permission_to_update
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseListSerializer)
import os


class WalletSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            password = data.get('password')
            if password:
                password = make_password(password)
            request = kwargs.get('_request')
            user = getattr(request, 'user')
            _data = {'password': password,
                     'user_id': getattr(user, 'id')}
            super(WalletSerializer, self).__init__(data=_data, **kwargs)
        else:
            super(WalletSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Wallet
        fields = '__all__'


class WalletResponseSerializer(BaseModelSerializer):
    class Meta:
        model = Wallet
        fields = ('user_id', 'balance', 'created', 'updated', 'extend')


class WalletDetailSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            if '_request' in kwargs:
                request = kwargs['_request']
                data['user_id'] = request.user.id
            super(WalletDetailSerializer, self).__init__(data=data, **kwargs)
        else:
            super(WalletDetailSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = WalletTradeDetail
        fields = '__all__'


class WalletDetailListSerializer(BaseListSerializer):
    child = WalletDetailSerializer()
