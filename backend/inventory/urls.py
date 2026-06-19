from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, ModuleViewSet, PermissionViewSet, admin_dashboard

router = DefaultRouter()
router.register(r'pages', PageViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'permissions', PermissionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
]
