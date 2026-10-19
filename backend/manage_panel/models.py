from django.db import models
from django.contrib.auth.models import User


class ManagePermission(models.Model):
    """Grants a staff user access to one section of the Manage panel.
    Superusers bypass this entirely (always full access); this only governs
    what a non-superuser "sub-admin" can see and do."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manage_permissions')
    section = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'section')

    def __str__(self):
        return f"{self.user} -> {self.section}"
