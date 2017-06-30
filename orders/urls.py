# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from orders import views

urlpatterns = [
    url(r'pay_orders_action/$', views.PayOrdersAction.as_view()),
    url(r'pay_orders_detail/$', views.PayOrdersDetail.as_view()),

    url(r'orders_list/$', views.OrdersList.as_view()),
    url(r'orders_detail/$', views.OrdersDetail.as_view()),

    # url(r'consume_orders_list/$', views.ConsumeOrdersList.as_view()),
    # url(r'consume_orders_detail/$', views.ConsumeOrdersDetail.as_view()),
    # url(r'pay_orders_detail/$', orders_view.UserDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


