from django.urls import path
from . import views

urlpatterns = [
    path('<int:posting_id>/', views.chat_room, name='chat_room'),
    path('inbox/', views.inbox, name='chat_inbox')
]