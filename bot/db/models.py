from django.db import models


class Reminder(models.Model):
    user_id = models.TextField()
    channel_id = models.TextField()
    message_id = models.TextField()
    message = models.TextField(default=None, blank=True, null=True)
    remind_time = models.DateTimeField()

    def __str__(self) -> str:
        return f"Reminder({self.remind_time})"
