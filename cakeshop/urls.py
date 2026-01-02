
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include
from django.views.static import serve
from cakeshop_app import views as customer_views
import os


urlpatterns = [
    path('', include('cakeshop_app.urls')),
    path('admin/', include('admin_app.urls')),
]

# Serve static files - use STATICFILES_DIRS for development (where AI-generated images are)
# This ensures logo1.png and other static files work correctly
static_root = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT
urlpatterns += [
    path('static/<path:path>', serve, {'document_root': static_root}),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Error handlers
handler404 = 'cakeshop_app.views.custom_404'
handler500 = 'cakeshop_app.views.custom_500'
