from rest_framework import serializers

from trips.models import Trip
from trips.services import ALMATY


class AlmatyDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        if value is not None:
            value = value.astimezone(ALMATY)
        return value.isoformat()


class TripSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='trip_id')
    start = AlmatyDateTimeField()
    end = AlmatyDateTimeField()

    class Meta:
        model = Trip
        fields = ('id', 'start', 'end', 'amount', 'payment', 'commission')
