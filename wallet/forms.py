# -*- encoding: utf-8 -*-
from horizon import forms


class WalletCreateForm(forms.Form):
    password = forms.CharField(min_length=6, max_length=6,
                               error_messages={
                                   'required': u'密码不能为空'
                               })


class WalletTradeActionForm(forms.Form):
    orders_id = forms.CharField(max_length=32)
    # 交易类型 1: 充值 2：消费 3: 取现
    trade_type = forms.IntegerField(min_value=1, max_value=3)
    # 交易金额
    amount_of_money = forms.CharField(max_length=16)


class WalletDetailListForm(forms.Form):
    page_index = forms.IntegerField(min_value=1)
    page_size = forms.IntegerField(min_value=1)
