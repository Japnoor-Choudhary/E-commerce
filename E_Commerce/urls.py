"""
URL configuration for E_Commerce project.
"""

from django.contrib import admin
from django.urls import path, include

# Swagger / OpenAPI imports
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ---------------- Admin ----------------
    path('admin/', admin.site.urls),

    # ---------------- Swagger / OpenAPI ----------------
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ---------------- App APIs ----------------
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('organization/', include('organization.urls')),
    path('orders/', include('orders.urls')),
    # path('inventory/', include('inventory.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)