from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from home.models import RoommatePost
from .models import Message

@login_required
def chat_room(request, posting_id):
    return render(request, 'chat/chat_room.html', {
        'posting_id': posting_id
    })

@login_required
def inbox(request):
    # Postings the user owns (as poster)
    my_posts = RoommatePost.objects.filter(user=request.user)
    posts_with_chats = [
        {
            'post': p,
            'message_count': Message.objects.filter(posting_id=p.id).count()
        }
        for p in my_posts
    ]

    # Postings the user has participated in (rentry)
    participated_ids = (
        Message.objects
        .filter(sender=request.user)
        .exclude(posting_id__in=my_posts.values_list('id', flat=True))
        .values_list('posting_id', flat=True)
        .distinct()
    )
    participated_chats = [
        {
            'posting_id': pid,
            'message_count': Message.objects.filter(posting_id=pid).count(),
            'last_message': Message.objects.filter(posting_id=pid).last(),
        }
        for pid in participated_ids
    ]

    return render(request, 'chat/inbox.html', {
        'posts_with_chats': posts_with_chats,
        'participated_chats': participated_chats,
    })