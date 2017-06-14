# -*- coding: utf8 -*-
from rest_framework.response import Response
from rest_framework import status

from users.wx_auth.serializers import AccessTokenSerializer, RandomStringSerializer
from users.wx_auth.models import WXRandomString
from users.wx_auth.forms import AuthCallbackForm
from users.wx_auth import settings as wx_auth_settings
from users.serializers import WXUserSerializer
from horizon.views import APIView
from horizon.http_requests import send_http_request

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

    def get(self, request, *args, **kwargs):
        """
        接受微信跳转页面传过来的code票据
        """
        form = AuthCallbackForm(request.data)
        if not form.is_valid():
            return Response(status=status.HTTP_200_OK)

        cld = form.cleaned_data
        result = self.verify_random_str(cld)
        if isinstance(result, Exception):
            return Response(status=status.HTTP_200_OK)
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
            return Response(status=status.HTTP_200_OK)

        # 存储token
        response_dict = json.loads(result.text)
        if 'access_token' not in response_dict:
            return Response(status=status.HTTP_200_OK)
        serializer = AccessTokenSerializer(data=response_dict)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(status=status.HTTP_200_OK)

        # 获取微信userinfo
        userinfo_params = wx_auth_settings.WX_AUTH_PARAMS['get_userinfo']
        userinfo_params['openid'] = response_dict['openid']
        userinfo_params['access_token'] = response_dict['access_token']
        userinfo_url = wx_auth_settings.WX_AUTH_URLS['get_userinfo']
        result = send_http_request(userinfo_url, userinfo_params)
        if isinstance(result, Exception) or not getattr(result, 'text'):
            return Response(status=status.HTTP_200_OK)

        # 存储数据到用户表
        userinfo_response_dict = json.loads(result.text)
        if 'openid' not in userinfo_response_dict:
            return Response(status=status.HTTP_200_OK)
        serializer = WXUserSerializer(data=userinfo_response_dict)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_200_OK)