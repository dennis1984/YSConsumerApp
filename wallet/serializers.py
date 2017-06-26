# -*- coding:utf8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from wallet.models import Wallet, WalletTradeDetail
from horizon.decorators import has_permission_to_update
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseListSerializer)
import os


class WalletSerializer(BaseModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'


class WalletDetailSerializer(BaseSerializer):
    class Meta:
        model = WalletTradeDetail
        fields = '__all__'


class WalletDetailListSerializer(BaseListSerializer):
    child = WalletDetailSerializer
