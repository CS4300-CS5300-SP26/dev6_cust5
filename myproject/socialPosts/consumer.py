import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from socialPosts.serializers import serialize_listing

from listings.models import RoommateListing  #Load the DB
from socialPosts.serializers import serialize_listing #Import socialPost listings

FEED_GROUP = "listing_feed"


class ListingFeedConsumer(AsyncWebsocketConsumer):
    """
    Real-time feed consumer for the BearEstate homepage.
    Every browser that has the homepage open joins the 'listing_feed'
    group.  When a new RoommateListing is saved, signals.py calls a
    group_send which triggers the listing_created handler below,
    pushing the card data to every connected client instantly.
    """

    async def connect(self):
        await self.channel_layer.group_add(FEED_GROUP, self.channel_name)
        await self.accept()

        # Populate the feed immediately on connection (last 20 posts)
        listings = await self.get_recent_listings()
        await self.send(text_data=json.dumps({
            "type": "initial_listings",
            "listings": listings,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(FEED_GROUP, self.channel_name)

    # Clients are receive-only for the feed
    async def receive(self, text_data=None, bytes_data=None):
        pass

    # Called by the channel layer when signals.py fires a group_send
    async def listing_created(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_listing",
            "listing": event["listing"],
        }))

    @database_sync_to_async
    def get_recent_listings(self, limit=20):
        from listings.models import RoommateListing   # adjust to your app name
        qs = (
            RoommateListing.objects
            .select_related("user", "user__profile")
            .filter(is_active=True)
            .order_by("-created_at")[:limit]
        )
        return [serialize_listing(lst) for lst in qs]


def serialize_listing(listing):
    """Shared serializer used by both the consumer and the signal."""
    profile = getattr(getattr(listing, "user", None), "profile", None)
    avatar  = (
        profile.avatar.url
        if (profile and getattr(profile, "avatar", None) and profile.avatar)
        else None   # JS will render an initials-bubble fallback
    )
    desc = listing.description or ""
    return {
        "id":          listing.pk,
        "slug":        getattr(listing, "slug", str(listing.pk)),
        "name":        listing.user.get_full_name() or listing.user.username,
        "location":    getattr(listing, "location", ""),
        "rent":        float(listing.monthly_rent) if getattr(listing, "monthly_rent", None) else None,
        "move_in":     str(listing.move_in_date) if getattr(listing, "move_in_date", None) else "",
        "type":        getattr(listing, "listing_type", ""),
        "description": (desc[:110] + "…") if len(desc) > 110 else desc,
        "avatar":      avatar,
        "status":      getattr(listing, "status", "Open"),
        "created_at":  listing.created_at.strftime("%-d %b %Y"),
    }