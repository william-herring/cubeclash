import uuid
from django.db import models
from django.conf import settings


class Battle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    battle_type = models.CharField(max_length=10, default='bo5')
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True)
    competitor_1 = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    competitor_2 = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='battle_competitor_2',
    )
    winner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name='battle_winner',
    )
    was_forfeited = models.BooleanField(default=False)

    def __str__(self):
        return f'Battle {self.id} initiated by {self.competitor_1}'


class Set(models.Model):
    set_type = models.CharField(max_length=10, default='bo5')
    battle = models.ForeignKey(
        Battle,
        on_delete=models.CASCADE,
        related_name='sets',
    )
    scramble_set = models.CharField(max_length=1000) # Semicolon-separated list of scrambles
    competitor_1_results = models.CharField(max_length=1000) # Semicolon-separated list of formatted results
    competitor_2_results = models.CharField(max_length=1000)