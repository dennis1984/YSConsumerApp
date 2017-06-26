# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from orders.serializers import (PayOrdersSerializer,
                                PayOrdersResponseSerializer,
                                ConsumeOrderSerializer)
from orders.permissions import IsOwnerOrReadOnly
from orders.models import (PayOrders, ConsumeOrders)
from orders.forms import (PayOrdersCreateForm,
                          PayOrdersUpdateForm)
from shopping_cart.serializers import ShoppingCartSerializer
from shopping_cart.models import ShoppingCart
from orders.pay import WXPay
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
        # 钱包支付
        if payment_mode == 1:
            pass
        elif payment_mode == 2:   # 微信支付
            _wxpay = WXPay(request, _instance)
            result = _wxpay.js_api()
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_206_PARTIAL_CONTENT)
        else:   # 支付宝支付
            pass
        return Response({}, status=status.HTTP_206_PARTIAL_CONTENT)


class BaseConsumeOrders(object):
    """
    子订单
    """
    def get_pay_orders_by_orders_id(self, pay_orders_id):
        return PayOrders.get_object(**{'orders_id': pay_orders_id})

    def make_consume_orders_id(self, pay_orders_id, index):
        return 'Z%s%03d' % (pay_orders_id, index)

    def create(self, pay_orders):
        """
        创建子订单
        """
        from decimal import Decimal

        if isinstance(pay_orders, PayOrders):
            serializer = PayOrdersSerializer(pay_orders)
        elif isinstance(pay_orders, dict):
            serializer = PayOrdersSerializer(data=pay_orders)
        else:
            _instance = self.get_pay_orders_by_orders_id(pay_orders)
            if isinstance(_instance, Exception):
                return TypeError('pay_orders must be PayOrders instance, dict or orders_id')
            serializer = PayOrdersSerializer(_instance)

        if hasattr(serializer, 'initial_data') and not serializer.is_valid():
            return serializer.errors
        _data = serializer.data
        if _data['payment_status'] != 200:
            return ValueError('The orders payment status must be 200!')

        pay_orders_id = _data['orders_id']
        dishes_detail_list = json.loads(_data['dishes_ids'])
        for index, business_dishes in enumerate(dishes_detail_list, 1):
            member_discount = 0
            other_discount = 0
            total_amount = 0
            for item in business_dishes['dishes_detail']:
                total_amount = Decimal(total_amount) + Decimal(item['price']) * item['count']
            payable = Decimal(total_amount) - Decimal(member_discount) - Decimal(other_discount)
            consume_data = {
                'orders_id': self.make_consume_orders_id(pay_orders_id, index),
                'user_id': _data['user_id'],
                'dishes_ids': json.dumps(business_dishes['dishes_detail']),
                'total_amount': str(total_amount),
                'member_discount': member_discount,
                'other_discount': other_discount,
                'payable': str(payable),
                'business_name': business_dishes['business_name'],
                'business_id': business_dishes['business_id'],
                'food_court_id': _data['food_court_id'],
                'food_court_name': _data['food_court_name'],
                'payment_mode': _data['payment_mode'],
                'orders_type': _data['orders_type'],
                'master_orders_id': pay_orders_id
            }
            serializer = ConsumeOrderSerializer(data=consume_data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise Exception(serializer.errors)
