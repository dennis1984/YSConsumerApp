# -*- coding:utf8 -*-

from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from coupons import views

urlpatterns = [
    url(r'^coupons_list/$', views.CouponsList.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)
