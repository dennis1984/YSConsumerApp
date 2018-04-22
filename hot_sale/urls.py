# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from hot_sale import views

urlpatterns = [
    url(r'^hot_sale_list/$', views.HotSaleList.as_view()),
    url(r'^dishes_detail/$', views.DishesDetail.as_view()),
    url(r'^food_court_list/$', views.FoodCourtList.as_view()),
    url(r'^food_court_detail/$', views.FoodCourtDetail.as_view()),
    url(r'^city_list/$', views.CityList.as_view()),

    url(r'^recommend_dishes_list/$', views.RecommendDishesList.as_view()),

    url(r'^get_nearest_food_court/$', views.FoodCourtNearestDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


