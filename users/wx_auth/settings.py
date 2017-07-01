#-*- coding:utf8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
import urllib
import os

from horizon import main

# 微信授权第三方登录接口域名
WX_AUTH_API_URL = 'https://api.weixin.qq.com/'

# 公众账号ID
APPID = 'wx55da5a50194f8c73'

# 应用授权作用域 （snsapi_userinfo代表：获取用户个人信息）
SCOPE = 'snsapi_userinfo'

# APP密钥
APPSECRET = '13d98f221c4c7197e51f799cd572c4f5'

# 授权类型
GRANT_TYPE = {
    'get_access_token': 'authorization_code',
    'refresh_token': 'refresh_token',
}

# 微信授权接口参数配置

# 微信授权登录回调地址 (前端页面)
REDIRECT_URI = 'http://yinshi.weixin.city23.com/login/wexincallback/'

# 网页授权登录链接
WX_AUTH_WEB_LINK = 'https://open.weixin.qq.com/connect/oauth2/authorize'

# 网页授权登录参数配置
WX_AUTH_PARAMS = {
    'get_code': {
        'appid': APPID,
        'redirect_uri': urllib.quote_plus(REDIRECT_URI),
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