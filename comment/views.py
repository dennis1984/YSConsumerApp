# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from comment.serializers import (CommentSerializer,
                                 CommentListSerializer,)
from comment.permissions import IsOwnerOrReadOnly
from comment.models import (Comment, )
from comment.forms import (CommentInputForm,
                           CommentListForm)
from orders.models import ConsumeOrders
from orders.serializers import (ConsumeOrdersSerializer,
                                OrdersListSerializer)

import json


class CommentAction(generics.GenericAPIView):
    """
    点评相关功能
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def is_orders_valid(self, request, orders_id):
        orders = ConsumeOrders.get_object(orders_id=orders_id)
        if isinstance(orders, Exception):
            return False, orders
        if orders.user_id != request.user.id:
            return False, Exception('Cannot perform this action')
        if orders.is_commented:
            return False, Exception('Cannot perform this action')
        return True, orders

    def is_request_data_valid(self, request):
        form = CommentInputForm(request.data)
        if not form.is_valid():
            return False, Exception(form.errors)
        cld = form.cleaned_data
        try:
            bz_comment = json.loads(cld['business_comment'])
            dishes_comment = json.loads(cld['dishes_comment'])
        except Exception as e:
            return False, e
        bz_comment_format = {'id': int,
                             'star': int}
        dishes_comment_format = {'dishes_id': int,
                                 'star': int}
        if not (isinstance(bz_comment, (list, tuple)) and
                isinstance(dishes_comment, (list, tuple))):
            return False, TypeError('The fields business_comment and dishes_comment '
                                    'type must be list')

        format_error = 'The fields %s data format is incorrect'
        date_error = 'The fields %s data is incorrect'
        for item in bz_comment:
            if not isinstance(item, dict):
                return False, TypeError(format_error % 'business_comment')
            if sorted(item.keys()) != sorted(bz_comment_format.keys()):
                return False, ValueError(date_error % 'business_comment')
            for key, value in item.items():
                if not isinstance(value, bz_comment_format[key]):
                    return False, TypeError(format_error % 'business_comment')
        for item in dishes_comment:
            if not isinstance(item, dict):
                return False, TypeError(format_error % 'dishes_comment')
            if sorted(item.keys()) != sorted(dishes_comment_format.keys()):
                return False, ValueError(date_error % 'dishes_comment')
            for key, value in item.items():
                if not isinstance(value, dishes_comment_format[key]):
                    return False, TypeError(format_error % 'dishes_comment')

        return True, cld

    def post(self, request, *args, **kwargs):
        """
        用户点评订单(订单为消费订单，即子订单)
        """
        result, data = self.is_request_data_valid(request)
        if not result:
            return Response({'Detail': data.args}, status=status.HTTP_400_BAD_REQUEST)

        cld = data
        result, orders = self.is_orders_valid(request, cld['orders_id'])
        if not result:
            return Response({'Detail': orders.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CommentSerializer(data={'orders': orders, 'cld': cld},
                                       request=request)
        if serializer.is_valid():
            serializer.save()
            # 标志订单状态为已评论
            orders_serializer = ConsumeOrdersSerializer()
            orders_serializer.set_commented(orders)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CommentList(generics.GenericAPIView):
    """
    用户点评列表
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_consume_orders_list(self, request):
        return ConsumeOrders.filter_finished_objects_detail(
            **{'user_id': request.user.id}
        )

    def post(self, request, *args, **kwargs):
        form = CommentListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        details = self.get_consume_orders_list(request)
        if isinstance(details, Exception):
            return Response({'Detail': details.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrdersListSerializer(data=details)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        result = serializer.list_data(**cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

