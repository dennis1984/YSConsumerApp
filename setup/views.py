# -*- coding: utf8 -*-
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from setup.serializers import (FeedbackSerializer)
from setup.forms import (FeedbackInputForm,)
from setup.permissions import IsOwnerOrReadOnly


class FeedbackAction(generics.GenericAPIView):
    """
    意见反馈
    """
    permissions = (IsOwnerOrReadOnly,)

    def post(self, request, *args, **kwargs):
        """
        发布反馈信息
        """
        form = FeedbackInputForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        cld = form.cleaned_data
        serializer = FeedbackSerializer(data=cld, request=request)
        if not serializer.is_valid():
            return Response({'Detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except Exception as e:
            return Response({'Detail': e.args}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status.HTTP_201_CREATED)
