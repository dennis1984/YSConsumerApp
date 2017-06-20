# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from shopping_cart import views as shopping_cart_views

urlpatterns = [
    url(r'shopping_cart_action/$', shopping_cart_views.ShoppingCartAction.as_view()),
    url(r'shopping_cart_list/$', shopping_cart_views.ShoppingCartList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


