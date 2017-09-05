# -*- encoding: utf-8 -*-
from horizon import forms


class CouponsListForm(forms.Form):
    start_amount = forms.FloatField(min_value=0.01, required=False)
    status = forms.ChoiceField(choices=((1, 1),
                                        (400, 3),),
                               required=False)
    page_size = forms.IntegerField(min_value=1, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class CouponsDetailForm(forms.Form):
    pk = forms.IntegerField(min_value=1)
