from django.shortcuts import redirect
from django.urls import reverse


class AdminLoginRequiredMiddleware:
    """Require Django auth staff/superuser for all /admin/ routes served by admin_app.
    Allows access to custom admin login/logout and static/media.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ''

        if path.startswith('/admin/'):
            # Allow custom admin signin/signout endpoints and Django admin login itself
            allowed = (
                path.startswith('/admin/signin/') or
                path.startswith('/admin/signout/') or
                path.startswith('/static/') or
                path.startswith('/media/')
            )
            if not allowed:
                user = getattr(request, 'user', None)
                if not (user and user.is_authenticated and (user.is_staff or user.is_superuser)):
                    login_url = reverse('admin_login')
                    return redirect(f"{login_url}?next={path}")

        response = self.get_response(request)
        return response


