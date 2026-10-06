from django.urls import path

from trips.views import DayDetailView, DayListView, TripCreateView

urlpatterns = [
    path('days/', DayListView.as_view()),
    path('days/<str:day>/', DayDetailView.as_view()),
    path('trips/', TripCreateView.as_view()),
]
