# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from orders import views

urlpatterns = [
    url(r'^confirm_pay_orders/$', views.PayOrdersConfirm.as_view()),
    url(r'^confirm_pay_orders_detail/$', views.PayOrdersConfirmDetail.as_view()),

    url(r'^pay_orders_action/$', views.PayOrdersAction.as_view()),
    url(r'^orders_list/$', views.OrdersList.as_view()),
    url(r'^orders_detail/$', views.OrdersDetail.as_view()),

    url(r'^confirm_consume/$', views.ConfirmConsumeAction.as_view()),
    url(r'^confirm_consume_finished_list/$', views.ConfirmConsumeList.as_view()),
    url(r'^confirm_consume_result/$', views.ConfirmConsumeResult.as_view()),

    url(r'^ys_pay_dishes_list/$', views.YSPayDishesList.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)


