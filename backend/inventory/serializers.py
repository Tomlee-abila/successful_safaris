from rest_framework import serializers
from .models import Page, Module, Permission

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    module_name = serializers.ReadOnlyField(source='module.name')
    
    class Meta:
        model = Permission
        fields = ['id', 'module', 'module_name', 'role', 'can_view', 'can_create', 'can_edit', 'can_delete', 'special_notes']

class ModuleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'name', 'permissions']
