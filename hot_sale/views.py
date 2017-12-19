# -*- coding: utf8 -*-
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from django.utils.six import BytesIO
from Business_App.bz_dishes.models import (Dishes,
                                           City,
                                           DISHES_MARK_DISCOUNT_VALUES)
from Business_App.bz_users.models import FoodCourt
from Business_App.bz_dishes.caches import DishesDetailCache
from hot_sale.serializers import (HotSaleSerializer,
                                  DishesDetailSerializer,
                                  DishesSerializer,
                                  FoodCourtListSerializer,
                                  FoodCourtSerializer,)
from hot_sale.forms import (HotSaleListForm,
                            DishesGetForm,
                            FoodCourtListForm,
                            FoodCourtGetForm,
                            RecommendDishesListForm)
from hot_sale.permissions import IsOwnerOrReadOnly
from hot_sale.caches import HotSaleCache
from collect.models import Collect

import random


class HotSaleList(generics.GenericAPIView):
    permissions = (IsOwnerOrReadOnly,)

    def get_hot_sale_list(self, request, **kwargs):
        # if kwargs['mark'] == 0:
        #     kwargs['mark__in'] = DISHES_MARK_DISCOUNT_VALUES
        #     kwargs.pop('mark')
        kwargs = {'mark': kwargs['mark'],
                  'food_court_id': kwargs['food_court_id']}
        return HotSaleCache().get_hot_sale_list(**kwargs)

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
            return Response({'Detail': object_data.args}, status=status.HTTP_400_BAD_REQUEST)

        serializer = HotSaleSerializer(data=object_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        results = serializer.list_data(**cld)
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class DishesDetail(generics.GenericAPIView):
    permissions = (IsOwnerOrReadOnly,)

    def get_dishes_detail(self, request, dishes_id):
        kwargs = {'dishes_id': dishes_id}
        result = DishesDetailCache().get_dishes_detail(**kwargs)
        if isinstance(result, Exception):
            return result
        is_collected = Collect.is_collected(request, dishes_id)
        result['is_collected'] = is_collected
        return result

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
        object_data = self.get_dishes_detail(request, cld['pk'])

        serializer = DishesDetailSerializer(data=object_data)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecommendDishesList(generics.GenericAPIView):
    """
    推荐菜品列表
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def get_recommend_dishes_list(self, request, **kwargs):
        details_list = Dishes.get_hot_sale_list(request, **kwargs)
        details_ids = []
        details_dict = {}
        for item in details_list:
            details_dict[item['id']] = item
            details_ids.append(item['id'])

        recommend_list = []
        for index in range(0, 4):
            if not details_ids:
                break
            dishes_id = random.choice(details_ids)
            recommend_list.append(details_dict[dishes_id])
            details_ids.remove(dishes_id)
        return recommend_list

    def post(self, request, *args, **kwargs):
        form = RecommendDishesListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        dishes_details = self.get_recommend_dishes_list(request, **cld)
        serializer = HotSaleSerializer(data=dishes_details)

        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        results = serializer.list_data()
        if isinstance(results, Exception):
            return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(results, status=status.HTTP_200_OK)


class FoodCourtList(generics.GenericAPIView):
    permission_classes = (IsOwnerOrReadOnly, )

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
    permission_classes = (IsOwnerOrReadOnly, )

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


class CityList(generics.GenericAPIView):
    """
    城市列表
    """
    permission_classes = (IsOwnerOrReadOnly,)

    def get_city_list(self):
        city_list = City.filter_objects()
        if isinstance(city_list, Exception):
            return []
        city_set = set([city.city for city in city_list])
        return sorted(list(city_set))

    def post(self, request, *args, **kwargs):
        city_list = self.get_city_list()
        return Response(city_list, status=status.HTTP_200_OK)


