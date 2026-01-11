"""
Custom permissions for Conversations app.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read: Anyone (authenticated or not)
    - Write: Only owner (created_by) or admin
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner or admin
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user or request.user.is_staff
        
        return request.user.is_staff


class IsOwner(permissions.BasePermission):
    """
    Custom permission: Only owner can access.
    """
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read: Anyone authenticated
    - Write: Only admin/staff
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
