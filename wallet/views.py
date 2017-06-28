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
                           WalletTradeDetail,
                           WALLET_TRADE_DETAIL_TRADE_TYPE_DICT)
from wallet.forms import (WalletDetailListForm,
                          WalletCreateForm,
                          WalletTradeActionForm)
from orders.models import (PayOrders,
                           ConsumeOrders,
                           PAY_ORDERS_TYPE)
from users.models import ConsumerUser


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


class WalletTradeAction(object):
    """
    钱包明细相关功能
    """
    def get_orders_instance(self, orders_id):
        kwargs = {'orders_id': orders_id}
        return PayOrders.get_success_orders(**kwargs)

    def get_user(self, user_id):
        return ConsumerUser.get_object(**{'pk': user_id})

    def recharge(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        充值
        """
        return self.create(orders_id=orders_id,
                           user_id=user_id,
                           amount_of_money=amount_of_money,
                           trade_type=WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['recharge'])

    def consume(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        消费
        """
        return self.create(orders_id=orders_id,
                           user_id=user_id,
                           amount_of_money=amount_of_money,
                           trade_type=WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['consume'])

    def withdrawals(self, orders_id=None, user_id=None, amount_of_money=None):
        """
        提现
        """
        return self.create(orders_id=orders_id,
                           user_id=user_id,
                           amount_of_money=amount_of_money,
                           trade_type=WALLET_TRADE_DETAIL_TRADE_TYPE_DICT['withdrawals'])

    def create(self, orders_id=None, user_id=None, trade_type=None, amount_of_money=None):
        """
        创建交易明细（包含：充值、消费和提现（暂不支持）的交易明细）
        """
        kwargs = {'orders_id': orders_id,
                  'user_id': user_id,
                  'trade_type': trade_type,
                  'amount_of_money': amount_of_money}
        form = WalletTradeActionForm(kwargs)
        if not form.is_valid():
            return form.errors

        cld = form.cleaned_data
        _instance = self.get_orders_instance(orders_id)
        if isinstance(_instance, Exception):
            return _instance
        _user = self.get_user(user_id)
        if isinstance(_user, Exception):
            return _user

        serializer = WalletDetailSerializer(data=cld)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        return serializer.errors
