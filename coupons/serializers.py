# -*- coding:utf8 -*-

from rest_framework import serializers
from horizon.serializers import (BaseListSerializer,
                                 BaseModelSerializer,
                                 BaseSerializer)
from coupons.models import (Coupons)


class CouponsSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            super(CouponsSerializer, self).__init__(data=data, **kwargs)
        else:
            super(CouponsSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Coupons
        fields = '__all__'


class CouponsDetailSerializer(BaseSerializer):
    coupons_id = serializers.IntegerField()
    status = serializers.IntegerField()

    name = serializers.CharField()
    type = serializers.IntegerField()
    type_detail = serializers.CharField()
    amount_of_money = serializers.CharField()
    expires = serializers.DateTimeField()
    created = serializers.DateTimeField()
    update = serializers.DateTimeField()


class CouponsDetailListSerializer(BaseListSerializer):
    child = CouponsDetailSerializer()

