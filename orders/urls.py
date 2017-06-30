# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from orders import views

urlpatterns = [
    url(r'pay_orders_action/$', views.PayOrdersAction.as_view()),
    url(r'orders_list/$', views.OrdersList.as_view()),
    url(r'orders_detail/$', views.OrdersDetail.as_view()),
    url(r'confirm_consume/$', views.ConfirmConsumeDetail.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)


