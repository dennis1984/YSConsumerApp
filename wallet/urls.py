# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from wallet import views

urlpatterns = [
    url(r'wallet_action/$', views.WalletAction.as_view()),
    url(r'wallet_detail/$', views.WalletDetail.as_view()),
    url(r'wallet_trade_list/$', views.WalletTradeDetailList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


