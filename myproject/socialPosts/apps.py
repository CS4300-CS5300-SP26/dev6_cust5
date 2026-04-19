#socialPosts/apps.py
from django.apps import AppConfig

class LiveFeedConfig(AppConfig):
    name = "socialPosts"

#Connects to each broadcast
    def ready(self):

#Connects to incomming signals
        import socialPosts.signals