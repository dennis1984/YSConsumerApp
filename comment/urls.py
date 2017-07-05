# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from comment import views

urlpatterns = [
    url(r'comment_action/$', views.CommentAction.as_view()),
    url(r'comment_list/$', views.CommentList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
