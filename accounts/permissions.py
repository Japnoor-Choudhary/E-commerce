from rest_framework.permissions import BasePermission


# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return request.user and request.user.is_superuser


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_superuser
        )


class IsCustomerOrGuest(BasePermission):
    """
    Permission for normal customers and guest users.
    Grants access if:
    - user is authenticated AND
    - user.is_customer == True OR user.is_guest == True
    """
    def has_permission(self, request, view):
        user = request.user
        return (
            user 
            and user.is_authenticated 
            and (getattr(user, "is_customer", False) or getattr(user, "is_guest", False))
        )