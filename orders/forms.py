# -*- encoding: utf-8 -*-
from horizon import forms


class PayOrdersCreateForm(forms.Form):
    dishes_ids = forms.CharField()
    # dishes_ids包含如下信息
    # dishes_ids = [{'dishes_id': 'xxx',
    #                'count': xxx}, {}, ...
    #              ]
    #
    # 生成订单途径
    gateway = forms.ChoiceField(choices=(('shopping_cart', 1), ('other', 2)),
                                error_messages={
                                   'required': u'更新菜品数量的方法不能为空'
                                })
