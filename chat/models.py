from django.db import models
from user.models import CustomUser

class Chat(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_chats',
        limit_choices_to={'role': 'user'}
    )
    specialist = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='specialist_chats',
        limit_choices_to={'role': 'specialist'}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'specialist'], name='unique_user_specialist_chat')
        ]

    def __str__(self):
        return f"Chat between {self.user} and {self.specialist}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} in {self.chat}"