from django.db import models

# Create your models here.
# OralCancerDetectionBackend/detector_api/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add additional fields for the user profile here
    # Example fields:
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    # You can add more fields as needed, e.g., profile picture, medical history details, etc.

    def __str__(self):
        return self.user.username

# Signal to automatically create a Profile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Signal to automatically save the Profile when the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()