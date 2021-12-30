from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from .services import join_auto_join_groups

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a profile whenever a User is created."""
    if created:
        Profile.objects.create(user=instance)
        join_auto_join_groups(instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save a profile whenever a User is saved."""
    instance.profile.save()
