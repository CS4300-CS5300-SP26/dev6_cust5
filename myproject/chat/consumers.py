import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from .filters import filter_message

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.posting_id = self.scope['url_route']['kwargs']['posting_id']
        self.room_group = f'chat_posting_{self.posting_id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        history = await self.get_history()
        for msg in history:
            await self.send(text_data=json.dumps(msg))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        raw_message = data['message']
        clean_message = filter_message(raw_message)
        
        user = self.scope['user']
        sender_name = user.username if user.is_authenticated else 'Anonymous'
        
        await self.save_message(user, clean_message)
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'chat_message',
                'message': clean_message,
                'sender': sender_name,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))

    @database_sync_to_async
    def save_message(self, user, content):
        Message.objects.create(
            posting_id=self.posting_id,
            sender=user if user.is_authenticated else None,
            sender_label=user.username if user.is_authenticated else 'anonymous',
            content=content
        )

    @database_sync_to_async
    def get_history(self):
        messages = Message.objects.filter(posting_id=self.posting_id)
        return [{'message': m.content, 'sender': m.sender_label} for m in messages]