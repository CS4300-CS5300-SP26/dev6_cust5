from django.db import models

# Create your models here.
def RoommatePost(models.Model):
    '''
    user = An instance from the Django built-in User class
    date = Date of post, using date from datetime package (Format: date(YYYY, MM, DD))
    message = Content of the roommate post
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    message = CharField(max_length = 200)