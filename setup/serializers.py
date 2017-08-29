# -*- coding:utf8 -*-
from rest_framework import serializers
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseDishesDetailSerializer)
from setup.models import Feedback
import os


class FeedbackSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, request=None, **kwargs):
        if data:
            update_dict = {'user_id': request.user.id,
                           'phone': request.user.phone,
                           'nickname': request.user.nickname}
            data.update(update_dict)
            super(FeedbackSerializer, self).__init__(data=data, **kwargs)
        else:
            super(FeedbackSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Feedback
        fields = '__all__'
