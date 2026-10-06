from django.db import models

CASH = 'cash'
CARD = 'card'
PAYMENTS = (
    (CASH, 'Наличные'),
    (CARD, 'Карта'),
)


class Trip(models.Model):
    trip_id = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment = models.CharField(max_length=8, choices=PAYMENTS)
    commission = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['start', 'trip_id']
        indexes = [
            models.Index(fields=['start'], name='trip_start_idx'),
        ]
