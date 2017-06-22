# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from shopping_cart.serializers import (ShoppingCartSerializer,
                                       ShoppingCartListSerializer)
from shopping_cart.permissions import IsOwnerOrReadOnly
from shopping_cart.models import ShoppingCart
from shopping_cart.forms import (ShoppingCartCreateForm,
                                 ShoppingCartDeleteForm,
                                 ShoppingCartUpdateForm,
                                 ShoppingCartListForm)
from Business_App.bz_dishes.models import Dishes


class ShoppingCartAction(generics.GenericAPIView):
    """
    shopping cart action
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_object_by_dishes_id(self, request, dishes_id):
        return ShoppingCart.get_object_by_dishes_id(request, dishes_id)

    def get_dishes_detail(self, request, dishes_id):
        return Dishes.get_dishes_detail_dict_with_user_info(pk=dishes_id)

    def post(self, request, *args, **kwargs):
        """
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        form = ShoppingCartCreateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        instance = self.get_object_by_dishes_id(request, cld['dishes_id'])
        dishes_detail = self.get_dishes_detail(request, cld['dishes_id'])
        if isinstance(dishes_detail, Exception):
            return Response({'Detail': dishes_detail.args}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(instance, ShoppingCart):
            serializer = ShoppingCartSerializer(instance)
            try:
                cld['method'] = 'add'
                serializer.update_instance_count(request, instance, cld)
            except:
                return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            cld['food_court_id'] = dishes_detail['food_court_id']
            serializer = ShoppingCartSerializer(data=cld, _request=request)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        更新购物车信息
        """
        form = ShoppingCartUpdateForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        obj = self.get_object_by_dishes_id(request, dishes_id=cld['dishes_id'])
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ShoppingCartSerializer(obj)
        try:
            serializer.update_instance_count(request, obj, cld)
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    def delete(self, request, *args, **kwargs):
        """
        删除购物车中某一个商品
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        form = ShoppingCartDeleteForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        obj = self.get_object_by_dishes_id(request, cld['dishes_id'])
        if isinstance(obj, Exception):
            return Response({'Detail': obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ShoppingCartSerializer(obj)
        try:
            serializer.delete_instance(request, obj)
        except:
            return Response({'Detail': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartList(generics.GenericAPIView):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartListSerializer
    permission_classes = (IsOwnerOrReadOnly, )

    def get_list_detail(self, request, food_court_id):
        return ShoppingCart.get_shopping_cart_detail_by_user_id(request, food_court_id)

    def post(self, request, *args, **kwargs):
        """
        用户购物车列表详情
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """
        form = ShoppingCartListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        cld = form.cleaned_data
        _data = self.get_list_detail(request, cld['food_court_id'])
        serializer = ShoppingCartListSerializer(data=_data)
        if serializer.is_valid():
            results = serializer.list_data(**cld)
            if isinstance(request, Exception):
                return Response({'Detail': results.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(results, status=status.HTTP_200_OK)
        else:
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
