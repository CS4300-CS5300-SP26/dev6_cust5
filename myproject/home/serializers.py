from rest_framework import serializers
from .models import RoommatePost

# Roommate posts serializer
class RoommatePostSerializer(serializers.ModelSerializer):
    '''
    Transforms data types from Django to json, so they appear on webpage/server.
    '''
    class Meta:
        model = RoommatePost
        
        # Specific fields from movie model being displayed on server
        fields = (
            'user',
            'date',
            'message',
            'status',
        )