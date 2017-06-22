# -*- coding:utf8 -*-
from PAY.wxpay.models import WXPayResult
from rest_framework import serializers


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WXPayResult
        fields = ('orders_id', 'request_data', 'extend')
        # fields = '__all__'


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WXPayResult
        fields = ('result_code', 'err_code', 'err_code_des', 'openid', 'is_subscribe',
                  'trade_type', 'bank_type', 'total_fee', 'settlement_total_fee',
                  'cash_fee', 'transaction_id', 'attach', 'time_end')

    def update_wxpay_result(self, instance, validated_data):
        """
        微信回调信息写入数据库
        """
        try:
            return super(ResponseSerializer, self).update(instance, validated_data)
        except Exception as e:
            return e


