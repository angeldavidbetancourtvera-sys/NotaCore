from functools import wraps
from typing import Any, Callable

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse


def role_required(*roles: str) -> Callable[[Callable[..., HttpResponse]], Callable[..., HttpResponse]]:
    allowed_roles = {role.upper() for role in roles}

    def decorator(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            user_role = getattr(request.user, 'rol', '') or ''
            if request.user.is_authenticated and user_role.upper() in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return _wrapped_view

    return decorator
