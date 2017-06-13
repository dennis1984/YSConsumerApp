# -*- encoding: utf-8 -*-
from django import forms


class Form(forms.Form):
    def is_valid(self):
        verify_result = super(Form, self).is_valid()
        if verify_result:
            self.cleaned_data_filter(self.cleaned_data)
        return verify_result

    def cleaned_data_filter(self, cld):
        for key in cld.keys():
            if isinstance(cld[key], basestring):
                if not cld[key]:
                    cld.pop(key)
            else:
                if cld[key] is None:
                    cld.pop(key)
        return cld
