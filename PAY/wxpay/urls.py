# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from PAY.wxpay import views

# app_name = 'WXPay'

urlpatterns = [
    # 扫描支付（模式二）
    url(r'^native_callback/$', views.NativeCallback.as_view(), name='native_callback'),
    # 公众号支付
    url(r'^jsapi_callback/$', views.NativeCallback.as_view()),
    # APP支付
    url(r'app_callback/$', views.NativeCallback.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


