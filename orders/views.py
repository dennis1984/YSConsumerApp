# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from orders.serializers import (PayOrdersSerializer,)
from orders.permissions import IsOwnerOrReadOnly
from orders.models import (PayOrders, ConsumeOrders)
from orders.forms import (PayOrdersCreateForm,)
from shopping_cart.serializers import ShoppingCartSerializer
from shopping_cart.models import ShoppingCart
import json


class PayOrdersAction(generics.GenericAPIView):
    """
    支付订单类
    """
    queryset = PayOrders.objects.all()
    serializer_class = PayOrdersSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def make_orders_by_dishes_ids(self, request, dishes_ids):
        return PayOrders.make_orders_by_dishes_ids(request, dishes_ids)

    def get_shopping_cart_instances_by_dishes_ids(self, request, dishes_ids):
        instances = []
        dishes_ids = [item['dishes_id'] for item in dishes_ids]
        for dishes_id in dishes_ids:
            _instance = ShoppingCart.get_object_by_dishes_id(request, dishes_id)
            if isinstance(_instance, Exception):
                continue
            instances.append(_instance)
        return instances

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
        _data = self.make_orders_by_dishes_ids(request, dishes_ids)
        if isinstance(_data, Exception):
            return Response({'Detail': _data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayOrdersSerializer(data=_data)
        if serializer.is_valid():
            serializer.save()
            # 清空购物车
            if cld['gateway'] == 'shopping_cart':
                self.clean_shopping_cart(request, dishes_ids)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#
# class UserDetail(generics.GenericAPIView):
#     queryset = ConsumerUser.objects.all()
#     serializer_class = UserDetailSerializer
#     # permission_classes = (IsAdminOrReadOnly, )
#
#     def post(self, request, *args, **kwargs):
#         user = ConsumerUser.get_user_detail(request)
#         if isinstance(user, Exception):
#             return Response({'Error': user.args}, status=status.HTTP_400_BAD_REQUEST)
#
#         serializer = UserDetailSerializer(user)
#         # if serializer.is_valid():
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#         # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
