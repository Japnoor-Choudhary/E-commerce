from rest_framework.permissions import BasePermission


class HasModelPermission(BasePermission):
    """
    Uses Django default permissions:
    add_model, change_model, delete_model, view_model
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if not request.user.is_authenticated:
            return False

        model = view.queryset.model
        perm = f"{model._meta.app_label}.view_{model._meta.model_name}"

        if request.method in ["POST"]:
            perm = f"{model._meta.app_label}.add_{model._meta.model_name}"
        elif request.method in ["PUT", "PATCH"]:
            perm = f"{model._meta.app_label}.change_{model._meta.model_name}"
        elif request.method == "DELETE":
            perm = f"{model._meta.app_label}.delete_{model._meta.model_name}"

        return request.user.has_perm(perm)
