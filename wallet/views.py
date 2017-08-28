# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from wallet.serializers import (WalletSerializer,
                                WalletDetailSerializer,
                                WalletDetailListSerializer,
                                WalletResponseSerializer)
from wallet.permissions import IsOwnerOrReadOnly
from wallet.models import (Wallet,
                           WalletTradeDetail)
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WalletUpdateForm)


class WalletAction(generics.GenericAPIView):
    """
    钱包相关功能
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_wallet_object(self, request):
        return Wallet.get_object(user_id=request.user.id)

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
            serializer_res = WalletResponseSerializer(serializer.data)
            if serializer_res.is_valid():
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        更改钱包密码
        """
        form = WalletUpdateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
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
            try:
                serializer.update_password(instance, cld)
            except Exception as e:
                return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)


class WalletDetail(generics.GenericAPIView):
    """
    钱包余额
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
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
        serializer = WalletResponseSerializer(_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WalletTradeDetailList(generics.GenericAPIView):
    """
    钱包明细
    """
    queryset = WalletTradeDetail.objects.all()
    serializer_class = WalletDetailSerializer
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

