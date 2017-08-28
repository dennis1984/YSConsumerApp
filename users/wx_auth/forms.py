# -*- encoding: utf-8 -*-
from horizon import forms


class AuthCallbackForm(forms.Form):
    code = forms.CharField(max_length=128)
    state = forms.CharField(max_length=128)
    callback_url = forms.URLField(max_length=256, required=False)

