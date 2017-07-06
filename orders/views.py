# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from orders.serializers import (PayOrdersSerializer,
                                PayOrdersResponseSerializer,
                                OrdersDetailSerializer,
                                OrdersListSerializer,
                                ConfirmConsumeSerializer)
from orders.permissions import IsOwnerOrReadOnly
from orders.models import (PayOrders, ConsumeOrders)
from orders.forms import (PayOrdersCreateForm,
                          PayOrdersUpdateForm,
                          OrdersListForm,
                          OrdersDetailForm,
                          ConfirmConsumeForm)
from shopping_cart.serializers import ShoppingCartSerializer
from shopping_cart.models import ShoppingCart
from orders.pay import WXPay, WalletPay

from horizon import main
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

    def make_orders_by_consume(self, request, dishes_ids):
        return PayOrders.make_orders_by_consume(request, dishes_ids)

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
            if not cld.get('payable'):
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
                    return Response({'Detail': results[1].args},
                                    status=status.HTTP_400_BAD_REQUEST)
            _data = self.make_orders_by_consume(request, dishes_ids)

        if isinstance(_data, Exception):
            return Response({'Detail': _data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayOrdersSerializer(data=_data)
        if serializer.is_valid():
            serializer.save()
            # 清空购物车
            if cld['gateway'] == 'shopping_cart':
                self.clean_shopping_cart(request, dishes_ids)

            orders_detail = serializer.instance.orders_detail
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


class OrdersDetail(generics.GenericAPIView):
    def get_orders_detail(self, request, cld):
        kwargs = {'user_id': request.user.id,
                  'orders_id': cld['orders_id']}
        if cld['orders_id'].startswith('Z'):
            return ConsumeOrders.get_object_detail(**kwargs)
        return PayOrders.get_object_detail(**kwargs)

    def post(self, request, *args, **kwargs):
        form = OrdersDetailForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        orders_detail = self.get_orders_detail(request, cld)
        if isinstance(orders_detail, Exception):
            return Response({'Detail': orders_detail.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrdersDetailSerializer(data=orders_detail)
        if not serializer.instance.is_valid():
            return Response({'Detail': serializer.instance.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.instance.data, status=status.HTTP_200_OK)


class OrdersList(generics.GenericAPIView):
    def get_all_list(self, request, cld):
        kwargs = {'user_id': request.user.id}
        pay_orders = PayOrders.filter_valid_orders_detail(**kwargs)
        consume_orders = ConsumeOrders.filter_objects_detail(**kwargs)
        pay_expired = PayOrders.filter_expired_orders_detail(**kwargs)
        orders_list = pay_orders + consume_orders
        orders_list.sort(key=lambda x: x['updated'], reverse=True)
        return orders_list + pay_expired

    def get_pay_list(self, request, cld):
        kwargs = {'user_id': request.user.id}
        return PayOrders.filter_valid_orders_detail(**kwargs)

    def get_consume_list(self, request, cld):
        kwargs = {'user_id': request.user.id}
        return ConsumeOrders.filter_consume_objects_detail(**kwargs)

    def get_finished_list(self, request, cld):
        kwargs = {'user_id': request.user.id}
        return ConsumeOrders.filter_finished_objects_detail(**kwargs)

    def get_expired_list(self, request, cld):
        kwargs = {'user_id': request.user.id}
        return PayOrders.filter_expired_orders_detail(**kwargs)

    def get_orders_list(self, request, cld):
        _filter = cld.get('filter', 'all')
        if _filter == 'all':
            return self.get_all_list(request, cld)
        elif _filter == 'pay':
            return self.get_pay_list(request, cld)
        elif _filter == 'consume':
            return self.get_consume_list(request, cld)
        elif _filter == 'finished':
            return self.get_finished_list(request, cld)
        elif _filter == 'expired':
            return self.get_expired_list(request, cld)

    def post(self, request, *args, **kwargs):
        form = OrdersListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        orders_list = self.get_orders_list(request, cld)
        serializer = OrdersListSerializer(data=orders_list)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        result_list = serializer.list_data(**cld)
        if isinstance(result_list, Exception):
            return Response({'Detail': result_list.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result_list, status=status.HTTP_200_OK)


class ConfirmConsumeDetail(generics.GenericAPIView):
    def is_valid_orders(self, request, orders_id):
        return ConsumeOrders.is_consume_of_payment_status(request, orders_id)

    def post(self, request, *args, **kwargs):
        random_str = main.make_random_number_of_string(13)
        _data = {'user_id': request.user.id,
                 'random_string': random_str}
        serializer = ConfirmConsumeSerializer(data=_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        # 二维码
        file_name = main.make_qrcode(random_str)
        static_url = main.make_static_url_by_file_path(file_name)
        # 条形码
        barcode_fname = main.make_barcode(random_str)
        barcode_static_url = main.make_static_url_by_file_path(barcode_fname)
        return Response({'qrcode_url': static_url,
                         'barcode_url': barcode_static_url,
                         'code': random_str},
                        status=status.HTTP_200_OK)


