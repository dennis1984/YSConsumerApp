# -*- coding: utf8 -*-
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from users.serializers import (UserSerializer,
                               UserInstanceSerializer,
                               UserDetailSerializer,
                               UserListSerializer,
                               IdentifyingCodeSerializer,
                               AdvertPictureListSerializer)
from users.permissions import IsOwnerOrReadOnly
from users.models import (ConsumerUser,
                          make_token_expire,
                          IdentifyingCode)
from users.forms import (CreateUserForm,
                         SendIdentifyingCodeForm,
                         VerifyIdentifyingCodeForm,
                         UpdateUserInfoForm,
                         SetPasswordForm,
                         WXAuthCreateUserForm,
                         AdvertListForm,
                         WXAuthLoginForm,)
from users.wx_auth.views import Oauth2AccessToken

from Business_App.bz_users.models import AdvertPicture

from horizon.views import APIView
from horizon.main import make_random_number_of_string
from horizon import main
import copy
import urllib


def verify_identifying_code(params_dict):
    """
    验证手机验证码
    """
    phone = params_dict['username']
    identifying_code = params_dict['identifying_code']

    instance = IdentifyingCode.get_object_by_phone(phone)
    if not instance:
        return Exception(('Identifying code is not existed or expired.',))
    if instance.identifying_code != identifying_code:
        return Exception(('Identifying code is incorrect.',))
    return True


class IdentifyingCodeAction(APIView):
    """
    send identifying code to a phone
    """
    def verify_phone(self, cld):
        instance = ConsumerUser.get_object(**{'phone': cld['username']})
        if cld['method'] == 'register':     # 用户注册
            if isinstance(instance, ConsumerUser):
                return Exception(('Error', 'The phone number is already registered.'))
        elif cld['method'] == 'forget_password':   # 忘记密码
            if isinstance(instance, Exception):
                return Exception(('Error', 'The user of the phone number is not existed.'))
        else:
            return Exception(('Error', 'Parameters Error.'))
        return True

    def post(self, request, *args, **kwargs):
        """
        发送验证码
        """
        form = SendIdentifyingCodeForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = self.verify_phone(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)

        identifying_code = make_random_number_of_string(str_length=6)
        serializer = IdentifyingCodeSerializer(data={'phone': cld['username'],
                                                     'identifying_code': identifying_code})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        # 发送到短线平台
        main.send_message_to_phone({'code': identifying_code}, (cld['username'],))
        return Response(status=status.HTTP_200_OK)


class IdentifyingCodeVerify(APIView):
    def post(self, request, *args, **kwargs):
        """
        验证手机验证码
        """
        form = VerifyIdentifyingCodeForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        result = verify_identifying_code(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'Result': result}, status=status.HTTP_200_OK)


class WXAuthAction(APIView):
    def get(self, request, *args, **kwargs):
        """
        微信第三方登录授权
        """
        from users.wx_auth import settings as wx_auth_settings
        from users.wx_auth.serializers import RandomStringSerializer

        form = WXAuthLoginForm(getattr(request, request.method))
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        wx_auth_params = copy.deepcopy(wx_auth_settings.WX_AUTH_PARAMS['get_code'])
        wx_auth_url = wx_auth_settings.WX_AUTH_URLS['get_code']
        end_params = wx_auth_params.pop('end_params')
        state = wx_auth_params['state']()
        wx_auth_params['state'] = state
        wx_auth_params['redirect_uri'] = urllib.quote_plus(
            wx_auth_params['redirect_uri'] % cld.get('callback_url', ''))
        return_url = '%s?%s%s' % (wx_auth_url,
                                  main.make_dict_to_verify_string(wx_auth_params),
                                  end_params)
        serializer = RandomStringSerializer(data={'random_str': state})
        if serializer.is_valid():
            serializer.save()
            return_data = {'wx_auth_url': return_url}
            return Response(return_data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserNotLoggedAction(APIView):
    """
    create user API
    """
    def get_object_by_username(self, username):
        return ConsumerUser.get_object(**{'phone': username})

    def post(self, request, *args, **kwargs):
        """
        用户注册
        """
        form = CreateUserForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = verify_identifying_code(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = ConsumerUser.objects.create_user(**cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserInstanceSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        """
        忘记密码
        """
        form = SetPasswordForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = verify_identifying_code(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object_by_username(cld['username'])
        if isinstance(instance, Exception):
            return Response({'Detail': instance.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(instance)
        try:
            serializer.update_password(request, instance, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer_response = UserInstanceSerializer(instance)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class IdentifyingCodeActionWithLogin(generics.GenericAPIView):
    """
    发送短信验证码（登录状态）
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def is_user_phone_binding(self, user):
        if not user.is_binding:
            return False, 'Can not perform this action, Please bind your phone first.'
        return True, None

    def post(self, request, *args, **kwargs):
        is_bind, error_message = self.is_user_phone_binding(request.user)
        if not is_bind:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)

        phone = request.user.phone
        identifying_code = make_random_number_of_string(str_length=6)
        serializer = IdentifyingCodeSerializer(data={'phone': phone,
                                                     'identifying_code': identifying_code})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        # 发送到短线平台
        main.send_message_to_phone({'code': identifying_code}, (phone,))
        return Response(status=status.HTTP_200_OK)


class WXAuthUserNotLoggedAction(generics.GenericAPIView):
    """
    微信用户注册（处于登录状态）
    """
    def get_object_by_openid(self, out_open_id):
        return ConsumerUser.get_object(**{'out_open_id': out_open_id})

    def post(self, request, *args, **kwargs):
        """
        用户注册（绑定手机号）
        """
        form = WXAuthCreateUserForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = verify_identifying_code(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_binding:
            return Response({'Detail': 'The phone is already binded'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(request.user)
        try:
            serializer.binding_phone_to_user(request, request.user, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        # 注册成功后返回token（即：登录状态）
        _token_dict = Oauth2AccessToken().get_token(request.user)
        if isinstance(_token_dict, Exception):
            return Response({'Detail': _token_dict.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_token_dict, status=status.HTTP_201_CREATED)


class UserAction(generics.GenericAPIView):
    """
    update user API
    """
    queryset = ConsumerUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_object_of_user(self, request):
        return ConsumerUser.get_object(**{'pk': request.user.id})

    def put(self, request, *args, **kwargs):
        """
        更新用户信息
        """
        form = UpdateUserInfoForm(request.data, request.FILES)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = self.get_object_of_user(request)
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(obj)
        try:
            serializer.update_userinfo(request, obj, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer_response = UserInstanceSerializer(obj)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class UserDetail(generics.GenericAPIView):
    queryset = ConsumerUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def post(self, request, *args, **kwargs):
        user = ConsumerUser.get_user_detail(request)
        if isinstance(user, Exception):
            return Response({'Error': user.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDetailSerializer(user)
        # if serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdvertPictureList(generics.GenericAPIView):
    """
    广告位图片列表
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def get_advert_objects(self, **kwargs):
        return AdvertPicture.filter_objects(**kwargs)

    def post(self, request, *args, **kwargs):
        form = AdvertListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        advert_instances = self.get_advert_objects(**cld)
        if isinstance(advert_instances, Exception):
            return Response({'Detail': advert_instances.args},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AdvertPictureListSerializer(advert_instances)
        datas = serializer.list_data()
        return Response(datas, status=status.HTTP_200_OK)


class AuthLogout(generics.GenericAPIView):
    """
    用户认证：登出
    """
    def post(self, request, *args, **kwargs):
        make_token_expire(request)
        return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ConsumerUser.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
