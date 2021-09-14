from django.db import models

class Reminder(models.Model):
    user_id = models.TextField()
    channel_id = models.TextField()
    message_id = models.TextField()
    message = models.TextField()
    remind_time = models.DateTimeField()
