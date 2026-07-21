"""
Permissions for taxonomy connector API.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Only allow access if user is accessing himself.
    """
    def has_object_permission(self, request, view, obj):
        return obj.username == request.user.username
