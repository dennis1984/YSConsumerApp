#-*- coding:utf8 -*-
from users.models import ConsumerUser
from rest_framework.request import Request
from django.db.models import Model


# def make_cache_expired(func):
#     def decorator(self, request, *args, **kwargs):
#         result = func(self, request, *args, **kwargs)
#         DishesCache().delete_dishes_list(request)
#         return result
#     return decorator


def has_permission_to_update(func):
    def decorator(self, request, *args, **kwargs):
        if not isinstance(request, Request):
            return func(self, request, *args, **kwargs)
        for item in [args] + [kwargs.values()]:
            if isinstance(item, Model):
                user_id = getattr(item, 'user_id')
                if user_id and user_id != request.user.id:
                    return Exception(('Error', 'Permission denied!'))
        return func(self, request, *args, **kwargs)
    return decorator
