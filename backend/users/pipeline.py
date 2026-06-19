"""Custom social-auth pipeline steps."""
from django.contrib.auth.models import Group
from .models import UserProfile


def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Ensure every social-login user has a UserProfile and is in the Customer group.
    Called at the end of the SOCIAL_AUTH_PIPELINE.
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    customer_group, _ = Group.objects.get_or_create(name='Customer')
    user.groups.add(customer_group)
