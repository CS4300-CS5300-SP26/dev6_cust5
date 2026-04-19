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

from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from socialPosts.serializers import serialize_listing

from listings.models import RoommateListing   # adjust to your app name
from socialPosts.serializers import serialize_listing  # ← same

FEED_GROUP = "listing_feed"


@receiver(post_save, sender=RoommateListing)
def broadcast_new_listing(sender, instance, created, **kwargs):
    """
    After a RoommateListing is created (not just updated), push the
    serialized data to every WebSocket client in the listing_feed group.
    """
    if not created:
        return  # only broadcast brand-new listings

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return  # channel layer not configured (e.g. during tests)

    payload = serialize_listing(instance)

    async_to_sync(channel_layer.group_send)(
        FEED_GROUP,
        {
            "type":    "listing_created",   # maps to ListingFeedConsumer.listing_created()
            "listing": payload,
        },
    )