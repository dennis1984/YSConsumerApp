# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from users import views as users_view

urlpatterns = [
    url(r'send_identifying_code/$', users_view.IdentifyingCodeAction.as_view()),
    url(r'verify_identifying_code/$', users_view.IdentifyingCodeVerify.as_view()),

    url(r'user_not_logged_action/$', users_view.UserNotLoggedAction.as_view()),
    url(r'user_action/$', users_view.UserAction.as_view()),
    url(r'user_detail/$', users_view.UserDetail.as_view()),

    url(r'logout/$', users_view.AuthLogout.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


