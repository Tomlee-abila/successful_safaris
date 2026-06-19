from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Modular Apps
    path('inventory/', include('inventory.urls')),
    path('shop/', include('shop.urls')),
    path('destinations/', include('destinations.urls')),
    path('packages/', include('packages.urls')),
    path('blog/', include('blog.urls')),
    path('crm/', include('crm.urls')),
    path('users/', include('users.urls')),
    path('social/', include('social_django.urls', namespace='social')),
    path('bookings/', include('bookings.urls')),
    
    # Core (Home, About, etc.)
    path('', include('core.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
