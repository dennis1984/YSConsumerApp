# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from collect import views

urlpatterns = [
    url(r'collect_action/$', views.CollectAction.as_view()),
    url(r'collect_list/$', views.CollectList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


