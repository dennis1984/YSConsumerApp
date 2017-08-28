# -*- encoding: utf-8 -*-
from horizon import forms


class PayOrdersConfirmForm(forms.Form):
    dishes_ids = forms.CharField(required=False)
    # dishes_ids包含如下信息
    # dishes_ids = [{'dishes_id': 'xxx',
    #                'count': xxx}, {}, ...
    #              ]
    #
    # 生成订单途径
    gateway = forms.ChoiceField(choices=(('shopping_cart', 1),
                                         ('yinshi_pay', 2),
                                         ('other', 3)),
                                error_messages={
                                    'required': u'Field ["gateway"] must in'
                                                u'[shopping_cart, yinshi_pay, other]'
                                })
    orders_type = forms.ChoiceField(choices=(('recharge', 1), ('consume', 2)))
    payable = forms.IntegerField(min_value=10, required=False)
    random_code = forms.CharField(min_length=6, max_length=32, required=False)


class PayOrdersCreateForm(forms.Form):
    dishes_ids = forms.CharField(required=False)
    # dishes_ids包含如下信息
    # dishes_ids = [{'dishes_id': 'xxx',
    #                'count': xxx}, {}, ...
    #              ]
    #
    # 生成订单途径
    gateway = forms.ChoiceField(choices=(('shopping_cart', 1),
                                         ('yinshi_pay', 2),
                                         ('other', 3)),
                                error_messages={
                                    'required': u'Field ["gateway"] must in'
                                                u'[shopping_cart, yinshi_pay, other]'
                                })
    orders_type = forms.ChoiceField(choices=(('recharge', 1), ('consume', 2)))
    payable = forms.IntegerField(min_value=10, required=False)
    random_code = forms.CharField(min_length=6, max_length=32, required=False)
    coupons_id = forms.IntegerField(min_value=1, required=False)
    notes = forms.CharField(max_length=120, required=False)


class PayOrdersUpdateForm(forms.Form):
    orders_id = forms.CharField(max_length=32)
    # 支付模式 1：钱包 2：微信支付 3：支付宝支付
    payment_mode = forms.IntegerField(min_value=1, max_value=3)


class OrdersListForm(forms.Form):
    filter = forms.ChoiceField(choices=(('all', 1),
                                        ('pay', 2),
                                        ('consume', 3),
                                        ('finished', 4),
                                        ('expired', 5)),
                               required=False)
    page_size = forms.IntegerField(min_value=1, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class OrdersDetailForm(forms.Form):
    orders_id = forms.CharField(max_length=32)


class ConfirmConsumeForm(forms.Form):
    orders_id = forms.CharField(max_length=32)


class ConfirmConsumeListForm(forms.Form):
    confirm_code = forms.CharField(min_length=13, max_length=32)


class YSPayDishesListForm(forms.Form):
    code = forms.CharField(min_length=6, max_length=32)
