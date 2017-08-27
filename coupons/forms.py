# -*- encoding: utf-8 -*-
from horizon import forms


class CouponsListForm(forms.Form):
    page_size = forms.IntegerField(min_value=1, required=False)
    page_index = forms.IntegerField(min_value=1, required=False)


class CouponsDetailForm(forms.Form):
    pk = forms.IntegerField(min_value=1)
