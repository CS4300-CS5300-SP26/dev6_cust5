from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    posting_id = models.IntegerField()
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    sender_label = models.CharField(max_length=50)  # 'user' or 'bot'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'[Posting {self.posting_id}] {self.sender_label}: {self.content[:40]}'