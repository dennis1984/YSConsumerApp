# -*- encoding: utf-8 -*-
from horizon import forms


class CollectActionForm(forms.Form):
    dishes_id = forms.IntegerField(min_value=1)


class CollectDeleteForm(forms.Form):
    dishes_id = forms.IntegerField(min_value=1)


class CollectListForm(forms.Form):
    page_index = forms.IntegerField(min_value=1, required=False)
    page_size = forms.IntegerField(min_value=1, required=False)

