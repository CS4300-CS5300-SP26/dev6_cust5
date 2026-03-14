from django.db import models
from django.contrib.auth.models import User

# Create your models here.
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
    message = models.CharField(max_length = 200)
    date = models.DateField()

    status = models.CharField(
        max_length=6,
        choices=Status.choices,
        default=Status.OPEN,
    )