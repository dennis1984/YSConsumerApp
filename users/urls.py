# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from users import views as users_view
from users.wx_auth import views as wx_auth_views

urlpatterns = [
    url(r'send_identifying_code/$', users_view.IdentifyingCodeAction.as_view()),
    url(r'verify_identifying_code/$', users_view.IdentifyingCodeVerify.as_view()),

    url(r'user_not_logged_action/$', users_view.UserNotLoggedAction.as_view()),
    url(r'wx_user_not_logged_action/$', users_view.WXAuthUserNotLoggedAction.as_view()),
    url(r'user_action/$', users_view.UserAction.as_view()),
    url(r'user_detail/$', users_view.UserDetail.as_view()),

    url(r'logout/$', users_view.AuthLogout.as_view()),

    # 微信授权登录
    url(r'wx_login/$', users_view.WXAuthAction.as_view()),
    # url(r'wxauth/callback/$', wx_auth_views.AuthCallback.as_view()),
    # 微信授权登录第三方回调地址
    url(r'^wxauth/callback/$', wx_auth_views.AuthCallback.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


