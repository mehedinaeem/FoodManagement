from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile with additional information required for the application.
    """
    DIETARY_CHOICES = [
        ('none', 'No specific diet'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('pescatarian', 'Pescatarian'),
        ('gluten-free', 'Gluten-Free'),
        ('keto', 'Keto'),
        ('other', 'Other'),
    ]
    
    BUDGET_RANGE_CHOICES = [
        ('low', 'Low ($0-50/week)'),
        ('medium', 'Medium ($50-100/week)'),
        ('high', 'High ($100+/week)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, help_text="Full name of the user")
    household_size = models.PositiveIntegerField(default=1, help_text="Number of people in household")
    dietary_preferences = models.CharField(
        max_length=50, 
        choices=DIETARY_CHOICES, 
        default='none',
        help_text="Dietary preferences or restrictions"
    )
    budget_range = models.CharField(
        max_length=20,
        choices=BUDGET_RANGE_CHOICES,
        default='medium',
        help_text="Weekly food budget range"
    )
    location = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Location (city, state, country) for future local features"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.full_name} ({self.user.email})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a UserProfile when a User is created.
    """
    if created:
        UserProfile.objects.create(
            user=instance,
            full_name=f"{instance.first_name} {instance.last_name}".strip() or instance.username
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the UserProfile when User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()

