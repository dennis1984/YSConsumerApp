# -*- coding: utf8 -*-
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from django.utils.six import BytesIO

from Business_App.bz_users.models import (FoodCourt,
                                          BusinessUser)
from Business_App.bz_dishes.models import (Dishes,
                                           DISHES_MARK_DISCOUNT_VALUES,
                                           )
from business.serializers import (BusinessUserSerializer,
                                  BusinessUserListSerializer,
                                  BusinessDishesListSerializer)

from business.forms import (BusinessUserListForm,
                            BusinessDishesListForm,
                            BusinessUserForm,
                            FoodCourtDishesListForm)

# from business.permissions import IsOwnerOrReadOnly
# from collect.models import Collect
from horizon import main
from horizon.views import APIView
import random


class BusinessUserList(APIView):
    """
    商家信息列表
    """

    def get_objects_list(self, **kwargs):
        return BusinessUser.get_object_list(**kwargs)

    # def get_food_court_list(self, **kwargs):
    #     return FoodCourt.filter_objects(**kwargs)

    def post(self, request, *args, **kwargs):
        form = BusinessUserListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _objects = self.get_objects_list(**cld)

        if isinstance(_objects, Exception):
            return Response({'Detail': _objects.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BusinessUserListSerializer(_objects)
        datas = serializer.list_data(**cld)
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response( datas, status=status.HTTP_200_OK)

class BusinessUserDetail(APIView):
    """
       商家信息
    """
    def get_object_detail(self,**kwargs):
        return BusinessUser.get_object(**kwargs)

    def post(self,request,*args,**kwargs):

        form = BusinessUserForm(request.data)
        if not  form.is_valid():
            return  Response({'Detail':form.errors},status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data

        try:
            obj = self.get_object_detail(**cld)
        except Exception as e:
            return Response({'Error': e.args}, status=status.HTTP_400_BAD_REQUEST)
        print obj
        serializer = BusinessUserSerializer(obj)
        print serializer
        return Response(serializer.data, status=status.HTTP_200_OK)

class BusinessDishesList(APIView):
    """
       商家菜品信息
    """

    def get_business_dishes_objects_list(self,request,**kwargs):

        return Dishes.get_business_dishes_list(**kwargs)

    def post(self,request,*args,**kwargs):

        form = BusinessDishesListForm(request.data)
        if not  form.is_valid():
            return  Response({'Detail':form.errors},status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _objects = self.get_business_dishes_objects_list(request,**cld)

        if isinstance(_objects, Exception):
            return Response({'Detail': _objects.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BusinessDishesListSerializer(data=_objects)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        datas = serializer.list_data(**cld)
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(datas, status=status.HTTP_200_OK)

class FoodCourtDishesList(APIView):
    """
       商场菜品信息
    """

    def get_food_court_dishes_objects_list(self,request,**kwargs):

        return Dishes.get_business_dishes_list(**kwargs)

    def post(self,request,*args,**kwargs):

        form = FoodCourtDishesListForm(request.data)
        if not  form.is_valid():
            return  Response({'Detail':form.errors},status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _objects = self.get_food_court_dishes_objects_list(request,**cld)

        if isinstance(_objects, Exception):
            return Response({'Detail': _objects.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BusinessDishesListSerializer(_objects)
        datas = serializer.list_data(**cld)
        if isinstance(datas, Exception):
            return Response({'Detail': datas.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(datas, status=status.HTTP_200_OK)



