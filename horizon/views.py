# -*- coding: utf8 -*-
from rest_framework.views import APIView as _APIView
from rest_framework.settings import APISettings, DEFAULTS, IMPORT_STRINGS
import copy


_default = copy.deepcopy(DEFAULTS)
_default.update(**{
    'PAY_CALLBACK_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',),
    'PAY_CALLBACK_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    )})
_import_strings = list(copy.deepcopy(IMPORT_STRINGS))
_import_strings.extend(['PAY_CALLBACK_AUTHENTICATION_CLASSES',
                        'PAY_CALLBACK_PERMISSION_CLASSES'])

api_settings = APISettings(None, _default, _import_strings)


class APIView(_APIView):
    authentication_classes = api_settings.PAY_CALLBACK_AUTHENTICATION_CLASSES
    permission_classes = api_settings.PAY_CALLBACK_PERMISSION_CLASSES
