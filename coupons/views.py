# -*- coding: utf8 -*-

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from coupons.serializers import (CouponsDetailListSerializer)
from coupons.permissions import IsOwnerOrReadOnly
from coupons.models import (Coupons)
from coupons.forms import (CouponsListForm)

from django.utils.timezone import now

import json


class CouponsList(generics.GenericAPIView):
    """
    优惠券详情列表
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_coupons_list(self, request):
        return Coupons.get_perfect_detail_list(user_id=request.user.id)

    def post(self, request, *args, **kwargs):
        """
        优惠券详情列表
        """
        form = CouponsListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        details = self.get_coupons_list(request)

        serializer = CouponsDetailListSerializer(data=details)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        datas = serializer.list_data(**cld)
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)

        return Response(datas, status=status.HTTP_200_OK)
