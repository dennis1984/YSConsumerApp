# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from wallet.serializers import (WalletSerializer,
                                WalletDetailListSerializer)
from wallet.permissions import IsOwnerOrReadOnly
from wallet.models import (Wallet,
                           WalletTradeDetail)
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WalletUpdateForm,
                          WalletPasswordCheckForm)
from users.models import IdentifyingCode


class WalletAction(generics.GenericAPIView):
    """
    钱包相关功能
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_wallet_object(self, request):
        return Wallet.get_object(user_id=request.user.id)

    def is_user_phone_binding(self, user):
        if not user.is_binding:
            return False, 'Can not perform this action, Please bind your phone first.'
        return True, None

    def does_wallet_password_exist(self, request):
        instance = self.get_wallet_object(request)
        if isinstance(instance, Exception):
            return False, None
        if not instance.password:
            return False, instance
        return True, instance

    def check_password_for_self(self, instance, password):
        return instance.check_password_for_self(password)

    def verify_identifying_code(self, request, identifying_code):
        """
        验证手机验证码
        """
        phone = request.user.phone

        instance = IdentifyingCode.get_object_by_phone(phone)
        if not instance:
            return False, Exception('Identifying code is not existed or expired.')
        if instance.identifying_code != identifying_code:
            return False, Exception('Identifying code is incorrect.')
        return True, None

    def post(self, request, *args, **kwargs):
        """
        创建用户钱包
        """
        form = WalletCreateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        serializer = WalletSerializer(data=cld, _request=request)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        更改钱包密码
        """
        form = WalletUpdateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        is_bind, error_message = self.is_user_phone_binding(request.user)
        if not is_bind:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        is_correct, error_obj = self.verify_identifying_code(request, cld['identifying_code'])
        if not is_correct:
            return Response({'Detail': error_obj.args}, status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_wallet_object(request)
        if isinstance(instance, Exception):
            serializer = WalletSerializer(data=cld, request=request)
            if not serializer.is_valid():
                return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            try:
                serializer.save()
            except Exception as e:
                return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = WalletSerializer(instance)
            cld['password'] = cld['new_password']
            try:
                serializer.update_password(instance, cld)
            except Exception as e:
                return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)


class WalletPasswordCheck(generics.GenericAPIView):
    """
    钱包密码验证
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def check_password(self, request, password):
        return Wallet.check_password(request, password)

    def post(self, request, *args, **kwargs):
        form = WalletPasswordCheckForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        is_correct = self.check_password(request, cld['password'])
        return Response({'result': is_correct}, status=status.HTTP_400_BAD_REQUEST)


class WalletPasswordWhetherSet(generics.GenericAPIView):
    """
    检查是否设置了钱包密码
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def get_wallet_object(self, request):
        return Wallet.get_object(user_id=request.user.id)

    def does_wallet_password_exist(self, request):
        instance = self.get_wallet_object(request)
        if isinstance(instance, Exception):
            return False
        if not instance.password:
            return False
        return True

    def post(self, request, *args, **kwargs):
        has_password = self.does_wallet_password_exist(request)
        return Response({'result': has_password}, status=status.HTTP_200_OK)


class WalletDetail(generics.GenericAPIView):
    """
    钱包余额
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_wallet_info(self, request):
        _wallet = Wallet.get_object(**{'user_id': request.user.id})
        if isinstance(_wallet, Exception):
            initial_dict = {'user_id': request.user.id,
                            'balance': '0'}
            _wallet = Wallet(**initial_dict)
        return _wallet

    def post(self, request, *args, **kwargs):
        """
        展示用户钱包余额
        """
        _instance = self.get_wallet_info(request)
        serializer = WalletSerializer(_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WalletTradeDetailList(generics.GenericAPIView):
    """
    钱包明细
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_details_list(self, request):
        kwargs = {'user_id': request.user.id}
        return WalletTradeDetail.get_success_list(**kwargs)

    def post(self, request, *args, **kwargs):
        form = WalletDetailListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _instances = self.get_details_list(request)
        if isinstance(_instances, Exception):
            return Response({'Detail': _instances.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = WalletDetailListSerializer(_instances)
        result = serializer.list_data(**cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

