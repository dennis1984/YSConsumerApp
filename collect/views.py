# -*- coding: utf8 -*-
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from collect.serializers import (CollectSerializer,
                                 CollectListSerializer,)
from collect.permissions import IsOwnerOrReadOnly
from collect.models import (Collect, )
from collect.forms import (CollectActionForm,
                           CollectListForm,
                           CollectDeleteForm)
from Business_App.bz_dishes.caches import DishesDetailCache


class CollectAction(generics.GenericAPIView):
    """
    钱包相关功能
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_collect_detail(self, request, cld):
        kwargs = {'user_id': request.user.id}
        if cld.get('pk'):
            kwargs['pk'] = cld['pk']
        if cld.get('dishes_id'):
            kwargs['dishes_id'] = cld['dishes_id']
        return Collect.get_object(**kwargs)

    def does_dishes_exist(self, dishes_id):
        result = DishesDetailCache().get_dishes_detail(dishes_id=dishes_id)
        if isinstance(result, Exception):
            return False
        return True

    def post(self, request, *args, **kwargs):
        """
        用户收藏商品
        """
        form = CollectActionForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        collect_obj = self.get_collect_detail(request, cld)
        if not isinstance(collect_obj, Exception):
            serializer = CollectSerializer(collect_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if not self.does_dishes_exist(cld['dishes_id']):
            return Response({'Detail': 'Dishes %s does not existed' % cld['dishes_id']},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = CollectSerializer(data=cld, request=request)
        if serializer.is_valid():
            result = serializer.save()
            if isinstance(result, Exception):
                return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        删除收藏的商品
        """
        form = CollectDeleteForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        collect_obj = self.get_collect_detail(request, cld)
        if isinstance(collect_obj, Exception):
            return Response({'Detail': collect_obj.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CollectSerializer(collect_obj)
        result = serializer.delete(request, collect_obj)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectList(generics.GenericAPIView):
    """
    用户收藏列表
    """
    permission_classes = (IsOwnerOrReadOnly, )

    def get_collects_list(self, request):
        collects = Collect.get_collect_list_with_user(request)
        if isinstance(collects, Exception):
            return collects
        collect_details = []
        for item in collects:
            dishes_detail = DishesDetailCache().get_dishes_detail(item.dishes_id)
            if isinstance(dishes_detail, Exception):
                continue
            collect_details.append(dishes_detail)
        return collect_details

    def post(self, request, *args, **kwargs):
        form = CollectListForm(request.data)
        if not form.is_valid():
            return Response({'Detail': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        _instances = self.get_collects_list(request)
        if isinstance(_instances, Exception):
            return Response({'Detail': _instances.args}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CollectListSerializer(data=_instances)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        result = serializer.list_data(**cld)
        if isinstance(result, Exception):
            return Response({'Detail': result.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

