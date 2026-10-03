from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        # Only create a UserProfile if one doesn't already exist
        if not hasattr(instance, 'userprofile'):
            UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if kwargs.get('raw', False):
        return
    # Only save the UserProfile if it exists
    if hasattr(instance, 'userprofile'):
        try:
            instance.userprofile.save()
        except Exception:
            # If there's an error saving, it might be because the profile doesn't exist
            # This can happen in some edge cases
            pass