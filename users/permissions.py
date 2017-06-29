# -*- coding:utf8 -*-
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    """
    自定义权限，只有创建者才能编辑
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the dishes.
        return obj.user_id == request.user.is_admin

    def has_permission(self, request, view):
        """
        自定义权限
        """
        return super(IsOwnerOrReadOnly, self).has_permission(request, view)