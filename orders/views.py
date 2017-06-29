# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from orders.serializers import (PayOrdersSerializer,
                                PayOrdersResponseSerializer,
                                ConsumeOrderSerializer,
                                ConsumeOrdersListSerializer,
                                ConsumeOrdersResponseSerializer)
from orders.permissions import IsOwnerOrReadOnly
from orders.models import (PayOrders, ConsumeOrders)
from orders.forms import (PayOrdersCreateForm,
                          PayOrdersUpdateForm,
                          ConsumeOrdersListForm,
                          ConsumeOrdersDetailForm)
from shopping_cart.serializers import ShoppingCartSerializer
from shopping_cart.models import ShoppingCart
from orders.pay import WXPay, WalletPay

import json


class PayOrdersAction(generics.GenericAPIView):
    """
    支付订单类
    """
    queryset = PayOrders.objects.all()
    serializer_class = PayOrdersSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_orders_by_orders_id(self, orders_id):
        return PayOrders.get_valid_orders(orders_id=orders_id)

    def make_orders_by_dishes_ids(self, request, dishes_ids):
        return PayOrders.make_orders_by_dishes_ids(request, dishes_ids)

    def make_orders_by_recharge(self, request, orders_type, payable):
        return PayOrders.make_orders_by_recharge(request, orders_type, payable)

    def get_shopping_cart_instances_by_dishes_ids(self, request, dishes_ids):
        instances = []
        for item in dishes_ids:
            dishes_id = item['dishes_id']
            kwargs = {'count': item['count']}
            _instance = ShoppingCart.get_object_by_dishes_id(request, dishes_id, **kwargs)
            if isinstance(_instance, Exception):
                return _instance
            instances.append(_instance)
        return instances

    def check_shopping_cart(self, request, dishes_ids):
        """
        检查购物车是否存在该物品
        """
        _instances = self.get_shopping_cart_instances_by_dishes_ids(request, dishes_ids)
        if isinstance(_instances, Exception):
            return False, _instances
        return True, None

    def clean_shopping_cart(self, request, dishes_ids):
        """
        清空购物车
        :param request: 
        :param dishes_ids: 
        :return: 
        """
        _instances = self.get_shopping_cart_instances_by_dishes_ids(request, dishes_ids)
        for _instance in _instances:
            sc_serializer = ShoppingCartSerializer(_instance)
            try:
                sc_serializer.delete_instance(request, _instance)
            except:
                continue

    def post(self, request, *args, **kwargs):
        """
        生成支付订单
        """
        form = PayOrdersCreateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        dishes_ids = None
        # 充值订单
        if cld['orders_type'] == 'recharge':
            if not cld['payable']:
                return Response({'Detail': '[payable] params error'},
                                status=status.HTTP_400_BAD_REQUEST)
            _data = self.make_orders_by_recharge(request, cld['orders_type'], cld['payable'])
        else:
            try:
                dishes_ids = json.loads(cld['dishes_ids'])
            except Exception as e:
                return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
            # 检查购物车
            if cld['gateway'] == 'shopping_cart':
                results = self.check_shopping_cart(request, dishes_ids)
                if not results[0]:
                    return Response({'Detail': results[1].args}, status=status.HTTP_400_BAD_REQUEST)
            _data = self.make_orders_by_dishes_ids(request, dishes_ids)

        if isinstance(_data, Exception):
            return Response({'Detail': _data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayOrdersSerializer(data=_data)
        if serializer.is_valid():
            serializer.save()
            # 清空购物车
            if cld['gateway'] == 'shopping_cart':
                self.clean_shopping_cart(request, dishes_ids)

            orders_detail = serializer.data
            dishes_detail = json.loads(orders_detail.pop('dishes_ids'))
            orders_detail['dishes_ids'] = dishes_detail
            serializer_response = PayOrdersResponseSerializer(data=orders_detail)
            if serializer_response.is_valid():
                return Response(serializer_response.data, status=status.HTTP_200_OK)

            return Response(serializer_response.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        选择支付方式
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        form = PayOrdersUpdateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        payment_mode = cld['payment_mode']
        _instance = self.get_orders_by_orders_id(cld['orders_id'])
        if isinstance(_instance, Exception):
            return Response({'Detail': _instance.args}, status=status.HTTP_400_BAD_REQUEST)

        if payment_mode == 1:      # 钱包支付
            wallet_pay = WalletPay(request, _instance)
            result = wallet_pay.wallet_pay()
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_206_PARTIAL_CONTENT)

        elif payment_mode == 2:   # 微信支付
            _wxpay = WXPay(request, _instance)
            result = _wxpay.js_api()
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_206_PARTIAL_CONTENT)

        else:   # 支付宝支付
            pass
        return Response({}, status=status.HTTP_206_PARTIAL_CONTENT)


class ConsumeOrdersList(generics.GenericAPIView):
    """
    用户子订单展示
    """
    def get_consume_orders_list(self, request):
        kwargs = {'user_id': request.user.id}
        return ConsumeOrders.filter_objects_detail(**kwargs)

    def post(self, request, *args, **kwargs):
        form = ConsumeOrdersListForm(request.data)
        if not form.is_valid():
            return Response({"Detail": form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        consume_orders = self.get_consume_orders_list(request)
        if isinstance(consume_orders, Exception):
            return Response({'Detail': consume_orders.args},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ConsumeOrdersListSerializer(data=consume_orders)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return_list = serializer.list_data(**cld)
        if isinstance(return_list, Exception):
            return Response({'Detail': return_list.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(return_list, status=status.HTTP_200_OK)


class ConsumeOrdersDetail(generics.GenericAPIView):
    def get_consume_orders_detail(self, request, cld):
        kwargs = {'orders_id': cld['consume_orders_id']}
        return ConsumeOrders.get_object_detail(**kwargs)

    def post(self, request, *args, **kwargs):
        form = ConsumeOrdersDetailForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _result = self.get_consume_orders_detail(request, cld)
        if isinstance(_result, Exception):
            return Response({'Detail': _result.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ConsumeOrdersResponseSerializer(data=_result)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)
