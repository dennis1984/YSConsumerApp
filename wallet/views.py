# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from wallet.serializers import (WalletSerializer,
                                WalletDetailSerializer,
                                WalletDetailListSerializer)
from wallet.permissions import IsOwnerOrReadOnly
from wallet.models import Wallet, WalletTradeDetail
from wallet.forms import (PayOrdersCreateForm,
                          PayOrdersUpdateForm)
from shopping_cart.serializers import ShoppingCartSerializer
from shopping_cart.models import ShoppingCart
from orders.pay import WXPay
import json


class WalletAction(generics.GenericAPIView):
    """
    钱包相关功能
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

