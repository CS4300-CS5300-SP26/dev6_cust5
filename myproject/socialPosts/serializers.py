# socialPosts/serializers.py

def serialize_listing(post):
    return {
        "id":          post.pk,
        "slug":        str(post.pk),
        "name":        post.user.get_full_name() or post.user.username,
        "location":    "",
        "rent":        float(post.rent) if post.rent else None,
        "move_in":     "",
        "type":        post.property_type,
        "description": (post.message[:110] + "…") if len(post.message) > 110 else post.message,
        "avatar":      None,
        "status":      post.status,
        "created_at":  post.date.strftime("%-d %b %Y"),
    }