# -*- encoding: utf-8 -*-
from horizon import forms


class CommentInputForm(forms.Form):
    orders_id = forms.CharField(min_length=12, max_length=32)
    business_comment = forms.CharField(max_length=256)
    # business_comment的数据格式为：
    # [{'id': 1,
    #   'star': 3},...
    # ]
    dishes_comment = forms.CharField(max_length=512)
    # dishes_comment的数据格式为：
    # [{'dishes_id':  1,
    #    'star': 3}, ....
    # ]
    messaged = forms.CharField(max_length=512, required=False)


class CommentListForm(forms.Form):
    page_index = forms.IntegerField(min_value=1, required=False)
    page_size = forms.IntegerField(min_value=1, required=False)

