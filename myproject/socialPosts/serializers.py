# socialPosts/serializers.py

def serialize_listing(listing):
    """Convert a RoommateListing ORM object to a JSON-safe dict."""
    profile = getattr(getattr(listing, "user", None), "profile", None)
    avatar  = (
        profile.avatar.url
        if (profile and getattr(profile, "avatar", None) and profile.avatar)
        else None
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