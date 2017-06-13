# -*- coding: utf8 -*-
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from users.serializers import (UserSerializer,
                               UserInstanceSerializer,
                               UserDetailSerializer,
                               UserListSerializer)
from users.permissions import IsOwnerOrReadOnly
from users.models import (ConsumerUser,
                          make_token_expire,
                          IdentifyingCode)
from users.forms import (CreateUserForm,
                         SendIdentifyingCodeForm,
                         VerifyIdentifyingCodeForm,
                         ChangePasswordForm,
                         SetPasswordForm)

from horizon.views import APIView
from horizon.main import make_random_number_of_string


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
        form = SendIdentifyingCodeForm(getattr(request, request.method))
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        result = self.verify_phone(cld)
        if isinstance(request, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)

        identifying_code = make_random_number_of_string(str_length=6)
        # 发送到短线平台
        return Response(status=status.HTTP_200_OK)


class IdentifyingCodeVerify(APIView):
    def post(self, request, *args, **kwargs):
        """
        验证手机验证码
        """
        form = VerifyIdentifyingCodeForm(getattr(request, request.method))
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        result = verify_identifying_code(cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'Result': result}, status=status.HTTP_200_OK)


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
        form = CreateUserForm(request.POST)
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
        form = SetPasswordForm(getattr(request, request.method))
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
        修改密码
        """
        form = ChangePasswordForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = self.get_object_of_user(request)
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(obj)
        try:
            serializer.update_password(request, obj, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer_response = UserInstanceSerializer(obj)
        return Response(serializer_response.data, status=status.HTTP_206_PARTIAL_CONTENT)


class UserDetail(generics.GenericAPIView):
    queryset = ConsumerUser.objects.all()
    serializer_class = UserDetailSerializer
    # permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, *args, **kwargs):
        user = ConsumerUser.get_user_detail(request)
        if isinstance(user, Exception):
            return Response({'Error': user.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDetailSerializer(user)
        # if serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class UserList(generics.GenericAPIView):
#     queryset = ConsumerUser.objects.all()
#     serializer_class = UserDetailSerializer
#     permission_classes = (IsOwnerOrReadOnly, )
#
#     def get_objects_list(self, request, **kwargs):
#         return ConsumerUser.get_objects_list(request, **kwargs)
#
#     def post(self, request, *args, **kwargs):
#         form = UserListForm(request.data)
#         if not form.is_valid():
#             return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
#
#         cld = form.cleaned_data
#         _objects = self.get_objects_list(request, **kwargs)
#         if isinstance(_objects, Exception):
#             return Response({'detail': _objects.args}, status=status.HTTP_400_BAD_REQUEST)
#
#         serializer = UserListSerializer(data=_objects)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         results = serializer.list_data(**cld)
#         if isinstance(results, Exception):
#             return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
#         return Response(results, status=status.HTTP_200_OK)


class AuthLogout(generics.GenericAPIView):
    """
    用户认证：登出
    """
    def post(self, request, *args, **kwargs):
        make_token_expire(request)
        return Response(status=status.HTTP_200_OK)


# class UserViewSet(viewsets.ModelViewSet):
#     """
#     """
#     queryset = ConsumerUser.objects.all().order_by('-date_joined')
#     serializer_class = UserSerializer
