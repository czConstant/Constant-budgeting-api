from django.db import models

from budgeting_pubsub.constants import SUB_LOG_STATUS


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SubLog(TimestampedModel):
    class Meta:
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['message_id', 'task']),
            models.Index(fields=['message_id', 'user_id']),
        ]

    user_id = models.IntegerField(null=True)
    task = models.CharField(max_length=100)
    message_id = models.BigIntegerField()
    data = models.TextField(null=True)
    response = models.TextField(null=True)
    status = models.CharField(max_length=50, choices=SUB_LOG_STATUS, default=SUB_LOG_STATUS.pending)
