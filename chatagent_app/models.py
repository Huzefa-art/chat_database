from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    ad_flag = models.BooleanField(default=False)
    verified = models.BooleanField(default=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username


class ChatSession(models.Model):
    """
    Represents a single chat tab/session.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True) 
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # useful for sorting recent chats

    def __str__(self):
        return f"{self.title} (ID: {self.id})"


class ChatMessage(models.Model):
    """
    Represents each message in a chat session.
    """
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    response_json = models.JSONField(null=True, blank=True)  # New field to store charts/data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]  

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
