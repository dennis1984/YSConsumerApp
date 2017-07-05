# -*- coding: utf8 -*-
from PAY.wxpay.wxpay import WXPAYJsApi
from PAY.wxpay import serializers as wx_serializers
from PAY.wxpay import settings as wx_settings
from PAY.wallet_pay.wallet_pay import WalletPay as Pay_WalletPay
from orders.models import PayOrders, BaseConsumeOrders
from users.models import ConsumerUser
from horizon import main
from django.conf import settings
import os
import json
from decimal import Decimal


class WXPay(object):
    def __init__(self, request, instance):
        if not isinstance(instance, PayOrders):
            raise Exception('Initialization Error')
        self.orders_id = instance.orders_id
        self.total_fee = int(Decimal(instance.payable) * 100)
        self.openid = request.user.out_open_id
        self.kwargs = {'detail': instance.dishes_ids_json_detail}

        self.body = u'%s-%s' % (instance.food_court_name, instance.orders_id)

    def js_api(self):
        """
        公众号支付
        """
        _wxpay = WXPAYJsApi(body=self.body,
                            out_trade_no=self.orders_id,
                            total_fee=self.total_fee,
                            openid=self.openid,
                            **self.kwargs)
        results = _wxpay.go_to_pay()
        if results.status_code != 200:
            return Exception(results.reason)
        # 解析xml
        xml_dict = main.anaysize_xml_to_dict(results.text)
        self.response_params = xml_dict
        if 'prepay_id' not in xml_dict:
            return Exception({'Detail': xml_dict.get('err_code', xml_dict['return_msg'])})
        if not self.is_response_params_valid():
            return Exception({'Detail': 'Sign is not valid'})

        # 存入数据库
        request_data = {'orders_id': self.orders_id,
                        'request_data': json.dumps(_wxpay.__dict__)}
        serializer = wx_serializers.RequestSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
        js_params_dict = {'appId': xml_dict['appid'],
                          'timeStamp': main.get_time_stamp(),
                          'nonceStr': main.make_random_char_and_number_of_string(str_length=32),
                          'package': 'prepay_id=%s' % xml_dict['prepay_id'],
                          'signType': wx_settings.SIGN_TYPE}
        pay_sign = main.make_sign_for_wxpay(js_params_dict)
        js_params_dict['paySign'] = pay_sign
        # return_dict = {'wx_jsapi': json.dumps(js_params_dict)}
        return js_params_dict

    def is_response_params_valid(self):
        """
        验证微信支付返回结果的有效性
        """
        if not isinstance(self.response_params, dict):
            return False
        _sign = self.response_params.pop('sign')
        maked_sign = main.make_sign_for_wxpay(self.response_params)

        if maked_sign == _sign:
            return True
        return False


class WalletPay(object):
    def __init__(self, request, orders):
        if not isinstance(orders, PayOrders):
            raise Exception('Initialization Error')
        self.orders = orders
        self.request = request

    def wallet_pay(self):
        """
        钱包支付
        """
        _wallet_pay = Pay_WalletPay(self.request, self.orders)
        result = _wallet_pay.go_to_pay()
        if isinstance(result, Exception):
            return result

        # 支付成功后，拆分主订单为子订单
        consume_result = BaseConsumeOrders().create(self.orders)
        if isinstance(consume_result, Exception):
            return consume_result
        return result
