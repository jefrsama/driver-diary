from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trips.serializers import TripSerializer
from trips.services import (
    TripConflict,
    TripError,
    build_summary,
    create_trip,
    parse_day,
    summary_payload,
    trip_days,
    trips_for_day,
)


class DayListView(APIView):
    def get(self, request):
        return Response({'dates': trip_days()})


class DayDetailView(APIView):
    def get(self, request, day):
        parsed = parse_day(day)
        if parsed is None:
            return Response(
                {'errors': {'date': 'Дата должна быть в формате YYYY-MM-DD'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        trips = trips_for_day(parsed)
        return Response({
            'date': parsed.isoformat(),
            'summary': summary_payload(build_summary(trips)),
            'trips': TripSerializer(trips, many=True).data,
        })


class TripCreateView(APIView):
    def post(self, request):
        try:
            trip, created = create_trip(request.data)
        except TripError as exc:
            return Response({'errors': exc.errors}, status=status.HTTP_400_BAD_REQUEST)
        except TripConflict:
            return Response(
                {'errors': {'id': 'Поездка с таким id уже есть и отличается от отправленной'}},
                status=status.HTTP_409_CONFLICT,
            )
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {'created': created, 'trip': TripSerializer(trip).data},
            status=code,
        )
