from rest_framework import permissions


class OwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and request.user == obj.user


class IsJobSeeker(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'job_seeker'

class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employer'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsVerifiedEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role == 'employer'
                and request.user.is_verified)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Chỉ cho phép chủ sở hữu CV chỉnh sửa, còn người khác chỉ đọc được.
    """

    def has_object_permission(self, request, view, obj):
        return obj.applicant == request.user

