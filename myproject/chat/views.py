from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from home.models import RoommatePost
from .models import Message

@login_required
def chat_room(request, posting_id, inquirer_id):
    return render(request, 'chat/chat_room.html', {
        'posting_id': posting_id,
        'inquirer_id': inquirer_id,
    })

@login_required
def inbox(request):
    my_posts = RoommatePost.objects.filter(user=request.user)

    # For each listing, build one entry per unique inquirer who has messaged it.
    # The poster must join the room keyed by the INQUIRER's id, not their own.
    posts_with_chats = []
    for p in my_posts:
        inquirer_ids = (
            Message.objects
            .filter(posting_id=p.id)
            .exclude(inquirer_id=None)
            .order_by('inquirer_id')
            .values_list('inquirer_id', flat=True)
            .distinct()
        )
        for iid in inquirer_ids:
            inquirer = User.objects.filter(id=iid).first()
            last_msg = Message.objects.filter(posting_id=p.id, inquirer_id=iid).last()
            posts_with_chats.append({
                'post': p,
                'inquirer_id': iid,
                'inquirer_name': inquirer.username if inquirer else f'User {iid}',
                'message_count': Message.objects.filter(posting_id=p.id, inquirer_id=iid).count(),
                'last_message': last_msg,
            })

    # Conversations where the current user is the inquirer.
    # Filter by inquirer_id=request.user.id so counts/previews are scoped correctly.
    my_post_ids = my_posts.values_list('id', flat=True)
    participated_ids = (
        Message.objects
        .filter(sender=request.user, inquirer_id=request.user.id)
        .exclude(posting_id__in=my_post_ids)
        .order_by('posting_id')
        .values_list('posting_id', flat=True)
        .distinct()
    )
    participated_chats = [
        {
            'posting_id': pid,
            'inquirer_id': request.user.id,
            'message_count': Message.objects.filter(posting_id=pid, inquirer_id=request.user.id).count(),
            'last_message': Message.objects.filter(posting_id=pid, inquirer_id=request.user.id).last(),
        }
        for pid in participated_ids
    ]

    return render(request, 'chat/inbox.html', {
        'posts_with_chats': posts_with_chats,
        'participated_chats': participated_chats,
    })