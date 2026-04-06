from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    """
    Extends Django's built-in User with optional contact info.
    Phone and email are not required (optional for now). They can become mandatory later on.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, default='')
    # Email is already on User, check if it's verified
    email_verified = models.BooleanField(default=False)
    # TOTP secret stored after the user completes 2-FA setup
    totp_secret = models.CharField(max_length=64, blank=True, default='')
    totp_enabled = models.BooleanField(default=False)
 
    class TwoFAMethod(models.TextChoices):
        NONE  = 'none',  'None'
        TOTP  = 'totp',  'Authenticator App'
        EMAIL = 'email', 'Email Code'
 
    two_fa_method = models.CharField(
        max_length=5,
        choices=TwoFAMethod.choices,
        default=TwoFAMethod.NONE,
    )
 
    def __str__(self):
        return f"Profile({self.user.username})"
 
 
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile whenever a new user is saved."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
 
class RoommatePost(models.Model):
    '''
    user = An instance from the Django built-in User class
    date = Date of post, using date from datetime package (Format: date(YYYY, MM, DD))
    message = Content of the roommate post
    status = Open or closed status of post
    '''
    class Status(models.TextChoices):
        ''' 
        Limits choices in status field to 'open' and 'closed'
        '''
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length = 500)
    date = models.DateField()

    status = models.CharField(
        max_length=6,
        choices=Status.choices,
        default=Status.OPEN,
    )
    rent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)      
    property_type = models.CharField(max_length=20, blank=True, default='')  

class Property(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    listing_type = models.CharField(max_length=10)
    property_type = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
