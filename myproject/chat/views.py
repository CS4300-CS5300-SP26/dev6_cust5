from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def chat_room(request, posting_id):
    return render(request, 'chat/chat_room.html', {
        'posting_id': posting_id
    })