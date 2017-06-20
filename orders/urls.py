# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from orders import views as orders_view

urlpatterns = [
    url(r'pay_orders_action/$', orders_view.PayOrdersAction.as_view()),
    # url(r'pay_orders_detail/$', orders_view.UserDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


