# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from wallet.serializers import (WalletSerializer,
                                WalletDetailSerializer,
                                WalletDetailListSerializer,
                                WalletResponseSerializer)
from wallet.permissions import IsOwnerOrReadOnly
from wallet.models import Wallet, WalletTradeDetail
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WalletTradeActionForm)
from orders.models import PayOrders, ConsumeOrders


class WalletAction(generics.GenericAPIView):
    """
    钱包相关功能
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = (IsOwnerOrReadOnly, )

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


class WalletDetail(generics.GenericAPIView):
    """
    钱包余额
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_wallet_info(self, request):
        return Wallet.get_object(**{'user_id': request.user.id})

    def post(self, request, *args, **kwargs):
        """
        展示用户钱包余额
        """
        _instance = self.get_wallet_info(request)
        serializer = WalletSerializer(_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WalletTradeAction(generics.GenericAPIView):
    """
    钱包明细相关功能
    """
    queryset = WalletTradeDetail.objects.all()
    serializer_class = WalletDetailSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_orders_instance(self, orders_id):
        kwargs = {'orders_id': orders_id}
        return PayOrders.get_success_orders(**kwargs)

    def post(self, request, *args, **kwargs):
        form = WalletTradeActionForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        _instance = self.get_orders_instance(cld['orders_id'])
        if isinstance(_instance, Exception):
            return Response({'Detail': _instance}, status=status.HTTP_400_BAD_REQUEST)
        serializer = WalletDetailSerializer(data=cld, _request=request)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'Detail': serializer.eerors}, status=status.HTTP_400_BAD_REQUEST)


class WalletTradeDetailList(generics.GenericAPIView):
    """
    钱包明细
    """
    queryset = WalletTradeDetail.objects.all()
    serializer_class = WalletDetailSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_details_list(self, request):
        return []

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

