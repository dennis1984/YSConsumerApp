from itertools import chain
from django.db import models
from django.conf import settings
from horizon.main import timezoneStringTostring
import urllib
import os
import copy


def model_to_dict(instance, fields=None, exclude=None):
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        # if not getattr(f, 'editable', False):
        #     continue
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)
    return data


class BaseManager(models.Manager):
    def get(self, *args, **kwargs):
        if 'status' not in kwargs:
            kwargs['status'] = 1
        instance = super(BaseManager, self).get(*args, **kwargs)
        return instance

    def filter(self, *args, **kwargs):
        if 'status' not in kwargs:
            kwargs['status'] = 1
        instances = super(BaseManager, self).filter(*args, **kwargs)
        return instances


def get_perfect_filter_params(cls, **kwargs):
    opts = cls._meta
    fields = ['pk']
    for f in opts.concrete_fields:
        fields.append(f.name)

    _kwargs = {}
    for key in kwargs:
        key_new = key.split('__')[0]
        if key_new in fields:
            _kwargs[key] = kwargs[key]
    return _kwargs


def get_perfect_detail_by_instance(instance):
    opts = instance._meta
    fields = []
    for f in opts.concrete_fields:
        fields.append(f)

    detail_dict = model_to_dict(instance)
    for f in fields:
        key = f.name
        if isinstance(f, models.DateTimeField):
            detail_dict[key] = timezoneStringTostring(detail_dict[key])
        elif isinstance(f, models.ImageField):
            image_str = urllib.unquote(str(detail_dict[key]))
            if image_str.startswith('http://') or image_str.startswith('https://'):
                detail_dict['%s_url' % key] = image_str
            else:
                detail_dict['%s_url' % key] = os.path.join(settings.WEB_URL_FIX,
                                                           'static',
                                                           image_str.split('static/', 1)[1])
            detail_dict.pop(key)
    return detail_dict


def get_perfect_detail_by_detail(cls, detail):
    opts = cls._meta
    fields = []
    for f in opts.concrete_fields:
        fields.append(f)

    detail_dict = copy.deepcopy(detail)
    for f in fields:
        key = f.name
        if key not in detail_dict:
            continue
        if isinstance(f, models.DateTimeField):
            detail_dict[key] = timezoneStringTostring(detail_dict[key])
        elif isinstance(f, models.ImageField):
            image_str = urllib.unquote(str(detail_dict[key]))
            if image_str.startswith('http://') or image_str.startswith('https://'):
                detail_dict['%s_url' % key] = image_str
            else:
                detail_dict['%s_url' % key] = os.path.join(settings.WEB_URL_FIX,
                                                           'static',
                                                           image_str.split('static/', 1)[1])
            detail_dict.pop(key)
    return detail_dict


