# -*- encoding: utf-8 -*-
from horizon import forms


class FeedbackInputForm(forms.Form):
    content = forms.CharField(min_length=10, max_length=120)
