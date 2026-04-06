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

        # Send history after connection is accepted
        history = await self.get_history()
        for msg in history:
            await self.send(text_data=json.dumps(msg))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        raw_message = data['message']

        # Run through word filter
        clean_message = filter_message(raw_message)

        # Save user message to DB
        await self.save_message('user', clean_message)

        # Generate and save bot reply
        bot_reply = self.bot_response(clean_message)
        await self.save_message('bot', bot_reply)

        # Broadcast both to the group
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'chat_message',
                'user_message': clean_message,
                'bot_reply': bot_reply,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'user_message': event['user_message'],
            'bot_reply': event['bot_reply'],
        }))

    def bot_response(self, message):
        return "Thanks for your message! The owner will be in touch shortly."

    @database_sync_to_async
    def save_message(self, sender_label, content):
        Message.objects.create(
            posting_id=self.posting_id,
            sender_label=sender_label,
            content=content
        )

    @database_sync_to_async
    def get_history(self):
            messages = Message.objects.filter(posting_id=self.posting_id)
            result = []
            for m in messages:
                if m.sender_label == 'user':
                    result.append({'user_message': m.content, 'bot_reply': ''})
                else:
                    result.append({'user_message': '', 'bot_reply': m.content})
            return result