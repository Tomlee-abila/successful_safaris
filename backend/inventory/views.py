from rest_framework import viewsets
from .models import Page, Module, Permission
from .serializers import PageSerializer, ModuleSerializer, PermissionSerializer

class PageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all().order_by('code')
    serializer_class = PageSerializer

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_fields = ['role', 'module__name']
