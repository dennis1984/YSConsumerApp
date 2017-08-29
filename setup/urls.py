# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from setup import views

urlpatterns = [
    url(r'^feedback_action/$', views.FeedbackAction.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


