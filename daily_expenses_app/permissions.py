from rest_framework import permissions


class UpdateOwnProfile(permissions.BasePermission):
    """Allow user to edit their own profile"""

    def has_object_permission(self, request, view, obj):
        """Check user if he is trying to edit their own profile"""
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.id == request.user.id


class IsOwner(permissions.BasePermission):
    """Allow users to edit their own categories"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
