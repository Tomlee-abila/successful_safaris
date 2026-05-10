from django.db import models

class Page(models.Model):
    ACCESS_CHOICES = [
        ('PUBLIC', 'Public'),
        ('USER', 'Registered User'),
        ('SUBADMIN', 'Sub-Admin'),
        ('SUPERADMIN', 'Super Admin'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    purpose = models.TextField()
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Module(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Permission(models.Model):
    ROLE_CHOICES = [
        ('VISITOR', 'Visitor'),
        ('USER', 'User'),
        ('SUBADMIN', 'Sub-Admin'),
        ('SUPERADMIN', 'Super Admin'),
    ]
    
    module = models.ForeignKey(Module, related_name='permissions', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    special_notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('module', 'role')

    def __str__(self):
        return f"{self.module.name} - {self.role}"
