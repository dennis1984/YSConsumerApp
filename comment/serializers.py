# -*- coding:utf8 -*-
from comment.models import Comment
from orders.models import ConsumeOrders
from horizon.decorators import has_permission_to_update
from horizon.serializers import (BaseSerializer,
                                 BaseModelSerializer,
                                 BaseListSerializer)
from horizon.main import make_random_number_of_string
from horizon.decorators import has_permission_to_update

import json
import os

COMMENT_BUSINESS_CN_DETAIL = {
    1: u'服务质量',
    2: u'卫生环境',
    3: u'出餐速度',
}


class CommentSerializer(BaseModelSerializer):
    def __init__(self, instance=None, data=None, **kwargs):
        if data:
            request = kwargs['request']
            orders = data['orders']
            cld = data['cld']

            dishes_ids = json.loads(orders.dishes_ids)
            dishes_ids_dict = {item['id']: item for item in dishes_ids}
            business_comment = json.loads(cld['business_comment'])
            dishes_comment = json.loads(cld['dishes_comment'])
            for item in dishes_comment:
                key = item['dishes_id']
                item['dishes_name'] = dishes_ids_dict[key]['title']
                item['image_url'] = dishes_ids_dict[key]['image_url']
            for item in business_comment:
                item['cn_name'] = COMMENT_BUSINESS_CN_DETAIL[item['id']]

            orders_data = {'user_id': request.user.id,
                           'orders_id': orders.orders_id,
                           'business_id': orders.business_id,
                           'business_name': orders.business_name,
                           'business_comment': json.dumps(business_comment),
                           'dishes_comment': json.dumps(dishes_comment),
                           'messaged': cld.get('messaged'), }
            kwargs.pop('request')
            super(CommentSerializer, self).__init__(data=orders_data, **kwargs)
        else:
            super(CommentSerializer, self).__init__(instance, **kwargs)

    class Meta:
        model = Comment
        fields = '__all__'

    def save(self, **kwargs):
        try:
            return super(CommentSerializer, self).save(**kwargs)
        except Exception as e:
            return e


class CommentListSerializer(BaseListSerializer):
    child = CommentSerializer()
