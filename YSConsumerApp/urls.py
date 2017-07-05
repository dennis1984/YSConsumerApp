# -*- coding:utf8 -*-
"""YSConsumerApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers
from users.wx_auth import views as wx_auth_views

### debug  ###
from users import views
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
### end debug  ###

urlpatterns = [
    ### debug  ###
    url(r'', include(router.urls)),
    ### end debug ###

    url(r'^api-auth', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    url(r'^auth/', include('users.urls', namespace='user')),
    url(r'^orders/', include('orders.urls', namespace='orders')),
    url(r'^shopping_cart/', include('shopping_cart.urls', namespace='shopping_cart')),
    url(r'^hot_sale/', include('hot_sale.urls', namespace='hot_sale')),
    url(r'^collect/', include('collect.urls', namespace='collect')),
    url(r'^comment/', include('comment.urls', namespace='comment')),

    # 钱包
    url(r'^wallet/', include('wallet.urls', namespace='wallet')),

    # 微信支付回调
    url(r'^wxpay/', include('PAY.wxpay.urls', namespace='wxpay')),
    # url(r'^alipay/', include('PAY.alipay.urls', namespace='alipay')),
]