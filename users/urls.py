# -*- coding:utf8 -*-
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from users import views as users_view
from users.wx_auth import views as wx_auth_views

urlpatterns = [
    url(r'^send_identifying_code/$', users_view.IdentifyingCodeAction.as_view()),
    url(r'^verify_identifying_code/$', users_view.IdentifyingCodeVerify.as_view()),

    url(r'^send_identifying_code_with_login/$', users_view.IdentifyingCodeActionWithLogin.as_view()),

    url(r'^user_not_logged_action/$', users_view.UserNotLoggedAction.as_view()),
    url(r'^user_action/$', users_view.UserAction.as_view()),
    url(r'^user_detail/$', users_view.UserDetail.as_view()),

    url(r'^advert_picture_list/$', users_view.AdvertPictureList.as_view()),

    url(r'^logout/$', users_view.AuthLogout.as_view()),

    # 微信授权登录
    url(r'^wx_login/$', users_view.WXAuthAction.as_view()),
    # 微信授权登录后获取token
    url(r'^wxauth/token/$', wx_auth_views.AuthCallback.as_view()),
    # 微信授权登录绑定手机号
    url(r'^wx_register/$', users_view.WXAuthUserNotLoggedAction.as_view()),

    # 获取config接口注入权限验证配置
    url(r'^get_js_sdk_permission_detail/$', wx_auth_views.JSSDKPermissonSignDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)


