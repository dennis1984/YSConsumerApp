# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from users.wx_auth.serializers import (AccessTokenSerializer,
                                       RandomStringSerializer,
                                       Oauth2AccessTokenSerializer,
                                       Oauth2RefreshTokenSerializer,
                                       JSAPITicketSerializer)
from users.wx_auth.models import (WXRandomString,
                                  WXAccessToken,
                                  WXJSAPITicket,
                                  Oauth2_Application,
                                  Oauth2_RefreshToken,
                                  Oauth2_AccessToken)
from users.wx_auth.forms import (AuthCallbackForm,
                                 JSSDKPermissonSignDetailForm)
from users.wx_auth import settings as wx_auth_settings
from users.serializers import WXUserSerializer
from users.models import ConsumerUser
from horizon.views import APIView
from horizon.http_requests import send_http_request
from horizon.main import make_time_delta
from horizon import main

from Admin_App.ad_coupons.models import CouponsConfig
from coupons.models import Coupons, CouponsAction

from oauthlib.common import generate_token
from django.utils.timezone import now
import json


class AuthCallback(APIView):
    """
    微信用户授权后回调
    """
    def verify_random_str(self, cld):
        """
        return: true: WXRandomString instance
                false: Exception
        """
        instance = WXRandomString.get_object_by_random_str(cld['state'])
        if isinstance(instance, Exception):
            return Exception(('Error', 'The random string is not existed.'))
        return instance

    def get_user_by_open_id(self, out_open_id):
        kwargs = {'out_open_id': out_open_id}
        return ConsumerUser.get_object(**kwargs)

    def mark_user_login(self, user):
        """
        标记用户已经登录
        """
        user.last_login = now()
        user.save()
        return user

    def send_coupons_to_new_user(self, user):
        # 派发首单优惠优惠券
        kwargs = {'type': 1, 'type_detail': 10}
        coupons = CouponsConfig.filter_objects(**kwargs)
        if isinstance(coupons, Exception):
            return None
        if len(coupons) <= 0:
            return None
        return CouponsAction().create_coupons([user], coupons[0])

    def post(self, request, *args, **kwargs):
        """
        接受微信跳转页面传过来的code票据
        """
        form = AuthCallbackForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = self.verify_random_str(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RandomStringSerializer(result)
        try:
            serializer.update(result, {'status': 1})
        except:
            pass

        # 获取access token
        access_token_params = wx_auth_settings.WX_AUTH_PARAMS['get_access_token']
        access_token_params['code'] = cld['code']
        access_token_url = wx_auth_settings.WX_AUTH_URLS['get_access_token']
        result = send_http_request(access_token_url, access_token_params)
        if isinstance(result, Exception) or not getattr(result, 'text'):
            return Response({'Detail': result.args},
                            status=status.HTTP_400_BAD_REQUEST)

        # 存储token
        response_dict = json.loads(result.text)
        if 'access_token' not in response_dict:
            return Response({'Detail': 'Get access token failed'},
                            status=status.HTTP_400_BAD_REQUEST)
        response_dict['state'] = cld['state']
        serializer = AccessTokenSerializer(data=response_dict)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response({'Detail': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        # 获取微信userinfo
        userinfo_params = wx_auth_settings.WX_AUTH_PARAMS['get_userinfo']
        userinfo_params['openid'] = response_dict['openid']
        userinfo_params['access_token'] = response_dict['access_token']
        userinfo_url = wx_auth_settings.WX_AUTH_URLS['get_userinfo']
        result = send_http_request(userinfo_url, userinfo_params)
        if isinstance(result, Exception) or not getattr(result, 'text'):
            return Response({'Detail': result.args},
                            status=status.HTTP_400_BAD_REQUEST)

        # 存储数据到用户表
        userinfo_response_dict = json.loads(result.text)
        if 'openid' not in userinfo_response_dict:
            return Response({'Detail': 'Get User Info failed'},
                            status=status.HTTP_400_BAD_REQUEST)

        # 检查用户是否存在及是否绑定了手机号
        _user = self.get_user_by_open_id(userinfo_response_dict['openid'])
        if isinstance(_user, Exception):       # 新用户
            serializer = WXUserSerializer(data=userinfo_response_dict)
            if not serializer.is_valid():
                return Response({'Detail': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            _user = self.get_user_by_open_id(userinfo_response_dict['openid'])
            is_binding = False

            # 派发首单优惠优惠券
            self.send_coupons_to_new_user(_user)
        else:
            if not _user.phone:        # 已经创建的用户，但是没有绑定手机号
                is_binding = False
            else:                      # 绑定完手机号的用户
                is_binding = True
        _token = Oauth2AccessToken().get_token(_user)
        if isinstance(_token, Exception):
            return Response({'Detail': _token.args},
                            status=status.HTTP_400_BAD_REQUEST)
        _token.update(**{'is_binding': is_binding})

        # 标记用户已经登录
        self.mark_user_login(_user)

        return Response(_token, status=status.HTTP_200_OK)


class Oauth2AccessToken(object):
    def get_user(self, user_id):
        kwargs = {'pk': user_id}
        return ConsumerUser.get_object(**kwargs)

    @property
    def application(self):
        try:
            return Oauth2_Application.objects.filter()[0]
        except Exception as e:
            return e

    def get_token(self, user):
        token_dict = {"access_token": generate_token(),
                      "token_type": "Bearer",
                      "expires_in": settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'],
                      "refresh_token": generate_token(),
                      "scope": ' '.join(settings.OAUTH2_PROVIDER['SCOPES'].keys()),
                      'out_open_id': user.out_open_id}
        if isinstance(self.application, Exception):
            return self.application

        access_token_data = {'token': token_dict['access_token'],
                             'expires': make_time_delta(seconds=token_dict['expires_in']),
                             'scope': token_dict['scope'],
                             'application': self.application,
                             'user': user}
        _access_token = Oauth2_AccessToken(**access_token_data)
        if not _access_token.is_valid():
            return ValueError('Access token is not valid')
        _access_token.save()
        refresh_token_data = {'token': token_dict['refresh_token'],
                              'access_token': _access_token,
                              'application': self.application,
                              'user': user}
        _refresh_token = Oauth2_RefreshToken(**refresh_token_data)
        _refresh_token.save()
        return token_dict


class JSSDKPermissonSignDetail(generics.GenericAPIView):
    """
    JS-SDK使用权限签名
    """
    def get_access_token(self, request):
        return WXAccessToken.get_object_by_openid(request.user.out_open_id)

    def get_jsapi_ticket(self, request, access_token):
        ticket = WXJSAPITicket.get_object(request)
        if ticket:
            return ticket.ticket

        # 没有JSAPI ticket，重新获取
        # 获取jsapi ticket
        access_url = wx_auth_settings.WX_JS_API_TICKET % access_token
        result = send_http_request(access_url=access_url, access_params={})
        if isinstance(result, Exception) or not getattr(result, 'text'):
            return result

        # 存储jsapi ticket
        response_dict = json.loads(result.text)
        if 'errcode' != 0:
            return Exception('Get jsapi ticket error.')

        init_data = {'ticket': response_dict['ticket'],
                     'expires_in': response_dict['expires_in'],
                     'open_id': request.user.out_open_id}
        serializer = JSAPITicketSerializer(data=init_data)
        if not serializer.is_valid():
            return Exception(serializer.errors)
        try:
            serializer.save()
        except Exception as e:
            return e

        return response_dict['ticket']

    def post(self, request, *args, **kwargs):
        """
        获取JS-SDK使用权限签名
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        form = JSSDKPermissonSignDetailForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        js_params_dict = {'appId': wx_auth_settings.APPID,
                          'timeStamp': main.get_time_stamp(),
                          'nonceStr': main.make_random_char_and_number_of_string(str_length=32),
                          'signature': None}

        access_token = self.get_access_token(request)
        if not access_token:
            return Response({'Detail': 'Access Token is expired!'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket = self.get_jsapi_ticket(request, access_token)
        if isinstance(ticket, Exception):
            return Response({'Detail': ticket.args}, status=status.HTTP_400_BAD_REQUEST)
        # 生成签名
        sign_dict = {'noncestr': js_params_dict['nonceStr'],
                     'jsapi_ticket': ticket,
                     'timestamp': js_params_dict['timeStamp'],
                     'url': cld['url']}
        sign_str = main.make_sign_base(sign_dict, sign_type='sha1')
        js_params_dict['signature'] = sign_str
        return Response(js_params_dict, status=status.HTTP_200_OK)
