from django import forms
from django.forms import widgets
from django.forms.widgets import force_text


class ChoiceField(forms.ChoiceField):
    def to_python(self, value):
        for key2, value2 in self.choices:
            if key2 == value or force_text(key2) == value:
                if isinstance(key2, int):
                    return int(value)
                elif isinstance(key2, float):
                    return float(value)
        return value

