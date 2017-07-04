# -*- coding:utf8 -*-
from collect.models import Collect
from horizon.decorators import has_permission_to_update
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseListSerializer)
from horizon.main import make_random_number_of_string
from horizon.decorators import has_permission_to_update
import os


class CollectSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            request = kwargs['request']
            data['user_id'] = request.user.id
            kwargs.pop('request')
            super(CollectSerializer, self).__init__(data=data, **kwargs)
        else:
            super(CollectSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Collect
        fields = '__all__'

    def save(self, **kwargs):
        try:
            return super(CollectSerializer, self).save(**kwargs)
        except Exception as e:
            return e

    @has_permission_to_update
    def delete(self, request, instance):
        validated_data = {'status': 2,
                          'dishes_id': '%s%08d' % (instance.dishes_id,
                                                   int(make_random_number_of_string(5)))}
        try:
            return super(CollectSerializer, self).update(instance, validated_data)
        except Exception as e:
            return e


class CollectListSerializer(BaseListSerializer):
    child = CollectSerializer()
