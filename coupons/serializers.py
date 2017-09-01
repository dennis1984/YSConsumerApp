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
    id = serializers.IntegerField()
    # coupons_id = serializers.IntegerField()
    status = serializers.IntegerField()

    name = serializers.CharField()
    type = serializers.IntegerField()
    amount_of_money = serializers.CharField(allow_blank=True, allow_null=True)
    discount_percent = serializers.IntegerField(allow_null=True)
    start_amount = serializers.CharField()
    description = serializers.CharField()
    expires = serializers.DateTimeField()
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()


class CouponsDetailListSerializer(BaseListSerializer):
    child = CouponsDetailSerializer()

