"""
signals.py

Wire this up in your app's AppConfig.ready():

    class ListingsConfig(AppConfig):
        name = "listings"
        def ready(self):
            import listings.signals  # noqa: F401

Requires:
    pip install channels channels-redis
    # redis running locally (or update CHANNEL_LAYERS to use InMemoryChannelLayer for dev)
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from home.models import RoommatePost
from socialPosts.serializers import serialize_listing

FEED_GROUP = "listing_feed"

@receiver(post_save, sender=RoommatePost)
def broadcast_new_listing(sender, instance, created, **kwargs):
    if getattr(settings, 'TESTING', False):
        return                          # skip WebSocket broadcast during tests
    if not created:
        return
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    payload = serialize_listing(instance)
    async_to_sync(channel_layer.group_send)(
        FEED_GROUP,
        {
            "type": "listing_created",
            "listing": payload,
        },
    )
