# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from orders.serializers import (PayOrdersSerializer,
                                PayOrdersResponseSerializer,
                                PayOrdersConfirmSerializer,
                                OrdersDetailSerializer,
                                OrdersListSerializer,
                                ConfirmConsumeSerializer,
                                ConsumeOrdersListSerializer,
                                YSPayDishesListSerializer)
from orders.permissions import IsOwnerOrReadOnly
from orders.models import (PayOrders,
                           ConsumeOrders,
                           ConfirmConsume,
                           ORDERS_ORDERS_TYPE)
from orders.forms import (PayOrdersCreateForm,
                          PayOrdersUpdateForm,
                          PayOrdersConfirmForm,
                          OrdersListForm,
                          OrdersDetailForm,
                          ConfirmConsumeListForm,
                          YSPayDishesListForm)
from coupons.models import Coupons
from shopping_cart.serializers import ShoppingCartSerializer
from shopping_cart.models import ShoppingCart
from orders.pay import WXPay, WalletPay
from Business_App.bz_orders.models import YinshiPayCode
from Business_App.bz_dishes.models import Dishes

from horizon import main
from horizon.models import get_perfect_detail_by_detail
import json


INPUT_ORDERS_GATEWAY = {
    'shopping_cart': 'shopping_cart',
    'yinshi_pay': 'yinshi_pay',
    'other': 'other',
}
INPUT_ORDERS_TYPE = {
    'recharge': 'recharge',
    'consume': 'consume',
}


class PayOrdersAction(generics.GenericAPIView):
    """
    支付订单类
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_orders_by_orders_id(self, orders_id):
        return PayOrders.get_valid_orders(orders_id=orders_id)

    def make_orders_by_consume(self, request, dishes_ids, coupons_id=None, _method=None):
        return PayOrders.make_orders_by_consume(request, dishes_ids,
                                                coupons_id=coupons_id,
                                                _method=_method)

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
            return False, _instances.args
        return True, None

    def clean_shopping_cart(self, request, dishes_ids):
        """
        清空购物车
        """
        _instances = self.get_shopping_cart_instances_by_dishes_ids(request, dishes_ids)
        if isinstance(_instances, Exception):
            return
        for _instance in _instances:
            sc_serializer = ShoppingCartSerializer(_instance)
            try:
                sc_serializer.delete_instance(request, _instance)
            except:
                continue

    def is_request_data_valid(self, **kwargs):
        if kwargs['gateway'] == INPUT_ORDERS_GATEWAY['yinshi_pay']:
            if 'random_code' not in kwargs:
                return False, 'Field ["random_code"] must be not empty when ' \
                              'gateway is "yinshi_pay"'
        if kwargs['orders_type'] == INPUT_ORDERS_TYPE['recharge']:
            if not kwargs.get('payable'):
                return False, 'Field ["payable"] data error.'
            if 'coupons_id' in kwargs:
                return False, 'Can not use coupons'
        if kwargs['orders_type'] == INPUT_ORDERS_TYPE['consume']:
            if 'dishes_ids' not in kwargs:
                return False, 'Field ["dishes_ids"] must be not empty when ' \
                              'orders_type is "consume".'
            try:
                json.loads(kwargs['dishes_ids'])
            except Exception as e:
                return False, e.args
        return True, None

    def is_user_binding(self, request):
        if not request.user.is_binding:
            return False, 'Can not perform this action, Please bind your phone first.'
        return True, None

    def post(self, request, *args, **kwargs):
        """
        生成支付订单
        """
        form = PayOrdersCreateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        is_valid, error_message = self.is_request_data_valid(**cld)
        if not is_valid:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)
        is_bind, error_message = self.is_user_binding(request)
        if not is_bind:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)

        dishes_ids = None
        # 充值订单
        if cld['orders_type'] == INPUT_ORDERS_TYPE['recharge']:
            _data = self.make_orders_by_recharge(request, cld['orders_type'], cld['payable'])
        else:
            dishes_ids = json.loads(cld['dishes_ids'])
            coupons_id = cld.get('coupons_id')
            # 检查购物车
            if cld['gateway'] == INPUT_ORDERS_GATEWAY['shopping_cart']:
                is_valid, error_message = self.check_shopping_cart(request, dishes_ids)
                if not is_valid:
                    return Response({'Detail': error_message},
                                    status=status.HTTP_400_BAD_REQUEST)
            _data = self.make_orders_by_consume(request, dishes_ids, coupons_id=coupons_id)

        if isinstance(_data, Exception):
            return Response({'Detail': _data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayOrdersSerializer(data=_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            serializer.save(**cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        # 清空购物车
        if cld['gateway'] == INPUT_ORDERS_GATEWAY['shopping_cart']:
            self.clean_shopping_cart(request, dishes_ids)

        orders_detail = serializer.instance.orders_detail
        serializer_response = PayOrdersResponseSerializer(data=orders_detail)
        if serializer_response.is_valid():
            return Response(serializer_response.data, status=status.HTTP_200_OK)
        return Response(serializer_response.errors, status=status.HTTP_400_BAD_REQUEST)

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

        is_bind, error_message = self.is_user_binding(request)
        if not is_bind:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        payment_mode = cld['payment_mode']
        _instance = self.get_orders_by_orders_id(cld['orders_id'])
        if isinstance(_instance, Exception):
            return Response({'Detail': _instance.args}, status=status.HTTP_400_BAD_REQUEST)

        # 检查优惠券是否已经使用过了
        if _instance.coupons_id:
            is_used = Coupons.is_used(pk=_instance.coupons_id)
            if is_used:
                return Response({'Detail': 'The coupon is used.'}, status=status.HTTP_400_BAD_REQUEST)

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


class PayOrdersConfirm(PayOrdersAction):
    """
    订单确认操作
    """
    def post(self, request, *args, **kwargs):
        """
        生成确认支付订单
        """
        form = PayOrdersConfirmForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        is_valid, error_message = self.is_request_data_valid(**cld)
        if not is_valid:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)
        is_bind, error_message = self.is_user_binding(request)
        if not is_bind:
            return Response({'Detail': error_message}, status=status.HTTP_400_BAD_REQUEST)

        # 消费订单
        if cld['orders_type'] != INPUT_ORDERS_TYPE['consume']:
            return Response({'Detail': 'orders type is not consume'},
                            status=status.HTTP_400_BAD_REQUEST)

        dishes_ids = json.loads(cld['dishes_ids'])
        # 检查购物车
        if cld['gateway'] == INPUT_ORDERS_GATEWAY['shopping_cart']:
            is_valid, error_message = self.check_shopping_cart(request, dishes_ids)
            if not is_valid:
                return Response({'Detail': error_message},
                                status=status.HTTP_400_BAD_REQUEST)

        _data = self.make_orders_by_consume(request, dishes_ids,
                                            _method='confirm_orders')
        if isinstance(_data, Exception):
            return Response({'Detail': _data.args}, status=status.HTTP_400_BAD_REQUEST)

        _data['dishes_ids'] = json.loads(_data['dishes_ids'])
        _data['request_data'] = cld
        serializer = PayOrdersConfirmSerializer(data=_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass


class OrdersDetail(generics.GenericAPIView):
    """
    订单详情
    """
    permission_classes = (IsOwnerOrReadOnly,)

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
    """
    订单列表
    """
    permission_classes = (IsOwnerOrReadOnly,)

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


class ConfirmConsumeAction(generics.GenericAPIView):
    """
    核销
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def is_valid_orders(self, request, orders_id):
        return ConsumeOrders.is_consume_of_payment_status(request, orders_id)

    def post(self, request, *args, **kwargs):
        # 先生成条形码
        random_str, barcode_fname = main.make_barcode()

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
        # barcode_fname = main.make_barcode(random_str)
        barcode_static_url = main.make_static_url_by_file_path(barcode_fname)
        return Response({'qrcode_url': static_url,
                         'barcode_url': barcode_static_url,
                         'code': random_str},
                        status=status.HTTP_200_OK)


class ConfirmConsumeList(generics.GenericAPIView):
    """
    获取核销结果
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def is_random_string_valid(self, request, random_string):
        kwargs = {'user_id': request.user.id,
                  'random_string': random_string}
        instance = ConfirmConsume.get_object(**kwargs)
        if isinstance(instance, Exception):
            return False
        return True

    def get_confirm_consume_list(self, request, confirm_code):
        kwargs = {'user_id': request.user.id,
                  'confirm_code': confirm_code}
        return ConsumeOrders.filter_finished_objects_detail(**kwargs)

    def post(self, request, *args, **kwargs):
        form = ConfirmConsumeListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        if not self.is_random_string_valid(request, cld['confirm_code']):
            return Response({'Detail': 'Random string does not exist or expired.'},
                            status=status.HTTP_400_BAD_REQUEST)

        instances = self.get_confirm_consume_list(request, cld['confirm_code'])
        if isinstance(instances, Exception):
            return Response({'Detail': instances.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ConsumeOrdersListSerializer(data=instances)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        datas = serializer.list_data()
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(datas, status=status.HTTP_200_OK)


class YSPayDishesList(generics.GenericAPIView):
    """
    吟食支付菜品详情
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def get_dishes_list(self, code):
        instance = YinshiPayCode.get_object(code=code)
        if isinstance(instance, Exception):
            return instance
        if instance.pay_orders_id:
            return Exception('Can not perform this action.')
        dishes_ids = json.loads(instance.dishes_ids)
        return self.get_perfect_dishes_details(dishes_ids)

    def get_perfect_dishes_details(self, dishes_ids):
        details = []
        for item in dishes_ids:
            kwargs = {'pk': item['dishes_id']}
            detail_dict = Dishes.get_dishes_detail_dict_with_user_info(**kwargs)
            detail_dict['count'] = item['count']
            details.append(detail_dict)
        return details

    def post(self, request, *args, **kwargs):
        form = YSPayDishesListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        dishes_list = self.get_dishes_list(code=cld['code'])
        if isinstance(dishes_list, Exception):
            return Response({'Detail': dishes_list.args}, status=status.HTTP_200_OK)

        serializer = YSPayDishesListSerializer(data=dishes_list)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        datas = serializer.list_data()
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(datas, status=status.HTTP_200_OK)
