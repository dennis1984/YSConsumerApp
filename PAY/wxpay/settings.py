# -*- coding:utf8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
import os

# 统一下单URL
UNIFIED_ORDER_URL = 'https://api.mch.weixin.qq.com/pay/unifiedorder'

# 公众账号ID
APPID = 'wx55da5a50194f8c73'

# 商户号
MCH_ID = '1448533802'

# 回调地址
NOTIFY_URL_DICT = {'NATIVE': os.path.join(settings.WEB_URL_FIX, 'wxpay/native_callback/'),
                   'JSAPI': os.path.join(settings.WEB_URL_FIX, 'wxpay/jsapi_callback/'),
                   'APP': os.path.join(settings.WEB_URL_FIX, 'wxpay/app_callback/'),
                   }
# NOTIFY_URL = reverse('WXPay:native_callback',
#                      current_app=self.request.resolver_match.namespace)

# 交易类型
TRADE_TYPE = {
    'js': 'JSAPI',        # h5页面支付
    'native': 'NATIVE',   # 扫描支付
    'app': 'APP'          # app端支付
}

# 支付密钥 （微信商户平台的密钥更改后，要及时更新此密钥，否则影响支付） # 非常重要的字段
KEY = 'a4f675f6452411e78769000c29d6fe14'

