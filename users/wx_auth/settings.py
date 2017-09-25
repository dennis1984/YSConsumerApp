# -*- coding:utf8 -*-

from django.conf import settings
from django.core.urlresolvers import reverse

from users.wx_auth.models import WXAPPInformation
from horizon import main

import urllib
import os


# 微信授权第三方登录接口域名
WX_AUTH_API_URL = 'https://api.weixin.qq.com/'


wx_app_info = WXAPPInformation.get_object()

# 公众账号ID
APPID = wx_app_info.app_id

# APP密钥
APPSECRET = wx_app_info.app_secret

# 应用授权作用域 （snsapi_userinfo代表：获取用户个人信息）
SCOPE = 'snsapi_userinfo'

# 授权类型
GRANT_TYPE = {
    'get_access_token': 'authorization_code',
    'refresh_token': 'refresh_token',
}

# 微信授权接口参数配置

# 微信授权登录回调地址 (前端页面)
if settings.ENVIRONMENT == 10:    # 开发环境
    REDIRECT_URI = 'http://yinshi.weixin.city23.com/login/wexincallback/?callback_url=%s'
elif settings.ENVIRONMENT == 20:  # 测试环境
    REDIRECT_URI = 'http://yinshi.weixin.city23.com/login/wexincallback/?callback_url=%s'
elif settings.ENVIRONMENT == 30:  # 生产环境
    REDIRECT_URI = 'http://yinshin.net/login/wexincallback/?callback_url=%s'
else:
    REDIRECT_URI = 'http://yinshi.weixin.city23.com/login/wexincallback/?callback_url=%s'

# 网页授权登录链接
WX_AUTH_WEB_LINK = 'https://open.weixin.qq.com/connect/oauth2/authorize'

# 网页授权登录参数配置
WX_AUTH_PARAMS = {
    'get_code': {
        'appid': APPID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'snsapi_userinfo',
        'state': main.make_random_char_and_number_of_string,
        'end_params': '#wechat_redirect',
    },
    'get_access_token': {
        'appid': APPID,
        'secret': APPSECRET,
        'code': None,
        'grant_type': GRANT_TYPE['get_access_token'],
    },
    'refresh_token': {
        'appid': APPID,
        'grant_type': GRANT_TYPE['refresh_token'],
        'refresh_token': None
    },
    'get_userinfo': {
        'openid': None,
        'lang': 'zh_CN',
        'access_token': None,
    }
}

# 微信授权登录url配置
WX_AUTH_URLS = {
    'get_code': WX_AUTH_WEB_LINK,
    'get_access_token': os.path.join(WX_AUTH_API_URL, 'sns/oauth2/access_token'),
    'refresh_token': os.path.join(WX_AUTH_API_URL, 'sns/oauth2/refresh_token'),
    'get_userinfo': os.path.join(WX_AUTH_API_URL, 'sns/userinfo'),
}
