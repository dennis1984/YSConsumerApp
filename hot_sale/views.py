# -*- coding: utf8 -*-
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from django.utils.six import BytesIO
from Business_App.bz_dishes.models import Dishes
from Business_App.bz_users.models import FoodCourt
from hot_sale.serializers import (HotSaleSerializer,DishesDetailSerializer,DishesSerializer,FoodCourtListSerializer,FoodCourtSerializer)
from hot_sale.forms import (HotSaleListForm,DishesGetForm,FoodCourtListForm,FoodCourtGetForm,)
from django.shortcuts import render

# Create your views here.
class HotSaleList(generics.GenericAPIView):
    queryset = Dishes.objects.all()
    serializer_class = HotSaleSerializer
    # permissions = (IsOwnerOrReadOnly,)

    def get_hot_sale_list(self, request, **kwargs):
        return Dishes.get_hot_sale_list(request, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'orders_id': '',
                        }
        :return:
        """
        form = HotSaleListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        object_data = self.get_hot_sale_list(request, **cld)
        if isinstance(object_data, Exception):
            return Response({'Error': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = HotSaleSerializer(data = object_data)
        if not serializer.is_valid():
            return Response({'Error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)

class DishesDetail(generics.GenericAPIView):
    # queryset = Dishes.objects.all()
    serializer_class = DishesDetailSerializer
    # permissions = (IsOwnerOrReadOnly,)

    def get_object(self, *args, **kwargs):
        return Dishes.get_hot_sale_object(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs: {'orders_id': '',
                        }
        :return:
        """
        form = DishesGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        object_data = self.get_object(**cld)
        return Response(object_data, status=status.HTTP_200_OK)

class FoodCourtList(generics.GenericAPIView):
    queryset = FoodCourt.objects.all()
    serializer_class = FoodCourtSerializer
    # permission_classes = (IsAdminOrReadOnly, )

    def get_object_list(self, **kwargs):
        return FoodCourt.get_object_list(**kwargs)


    def post(self, request, *args, **kwargs):
        """
        带分页功能
        返回数据格式为：{'count': 当前返回的数据量,
                       'all_count': 总数据量,
                       'has_next': 是否有下一页,
                       'data': [{
                                 FoodCourt model数据
                                },...]
                       }
        """
        form = FoodCourtListForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        try:
            filter_list = self.get_object_list(**cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        # serializer = FoodCourtSerializer(filter_list, many=True)
        serializer = FoodCourtListSerializer(filter_list)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Error': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class FoodCourtDetail(generics.GenericAPIView):

    serializer_class = FoodCourtSerializer
    # permission_classes = (IsAdminOrReadOnly, )

    def get_object_detail(self, **kwargs):
        return FoodCourt.get_object(**kwargs)


    def post(self, request, *args, **kwargs):
        """
        获取美食城的详情
        """
        form = FoodCourtGetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        try:
            obj = self.get_object_detail(**cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = FoodCourtSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
