# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from hot_sale import views as hot_sale_view

urlpatterns = [
    url(r'hot_sale_list/$', hot_sale_view.HotSaleList.as_view()),
    url(r'dishes_detail/$', hot_sale_view.DishesDetail.as_view()),
    url(r'food_court_list/$', hot_sale_view.FoodCourtList.as_view()),
    url(r'food_court_detail/$', hot_sale_view.FoodCourtDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


