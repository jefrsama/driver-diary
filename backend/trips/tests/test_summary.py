from datetime import date
from decimal import Decimal

from django.test import TestCase

from trips.services import build_summary, create_trip, trips_for_day


def trip(trip_id, amount, payment, commission, start='2026-10-01T08:00:00+05:00', end='2026-10-01T08:20:00+05:00'):
    create_trip({
        'id': trip_id,
        'start': start,
        'end': end,
        'amount': amount,
        'payment': payment,
        'commission': commission,
    })


class SummaryTests(TestCase):
    def test_example_day(self):
        trip('t1', 2400, 'card', 360, '2026-10-01T08:10:00+05:00', '2026-10-01T08:32:00+05:00')
        trip('t2', 1500, 'cash', 225, '2026-10-01T09:05:00+05:00', '2026-10-01T09:20:00+05:00')
        summary = build_summary(trips_for_day(date(2026, 10, 1)))
        self.assertEqual(summary['trip_count'], 2)
        self.assertEqual(summary['revenue'], Decimal('3900.00'))
        self.assertEqual(summary['commission'], Decimal('585.00'))
        self.assertEqual(summary['net'], Decimal('3315.00'))
        self.assertEqual(summary['cash'], {'trip_count': 1, 'revenue': Decimal('1500.00')})
        self.assertEqual(summary['card'], {'trip_count': 1, 'revenue': Decimal('2400.00')})

    def test_empty_day_is_zero(self):
        summary = build_summary(trips_for_day(date(2026, 10, 3)))
        self.assertEqual(summary['trip_count'], 0)
        self.assertEqual(summary['revenue'], Decimal('0.00'))
        self.assertEqual(summary['commission'], Decimal('0.00'))
        self.assertEqual(summary['net'], Decimal('0.00'))
        self.assertEqual(summary['cash']['revenue'], Decimal('0.00'))
        self.assertEqual(summary['card']['revenue'], Decimal('0.00'))

    def test_decimal_amounts(self):
        trip('d1', '0.10', 'cash', '0.01')
        trip('d2', '0.20', 'card', '0.02', '2026-10-01T09:00:00+05:00', '2026-10-01T09:10:00+05:00')
        summary = build_summary(trips_for_day(date(2026, 10, 1)))
        self.assertEqual(summary['revenue'], Decimal('0.30'))
        self.assertEqual(summary['commission'], Decimal('0.03'))
        self.assertEqual(summary['net'], Decimal('0.27'))

    def test_other_day_is_not_included(self):
        trip('t1', 2400, 'card', 360)
        trip('t9', 1000, 'cash', 100, '2026-10-02T01:30:00+05:00', '2026-10-02T01:50:00+05:00')
        first = build_summary(trips_for_day(date(2026, 10, 1)))
        second = build_summary(trips_for_day(date(2026, 10, 2)))
        self.assertEqual(first['trip_count'], 1)
        self.assertEqual(first['revenue'], Decimal('2400.00'))
        self.assertEqual(second['trip_count'], 1)
        self.assertEqual(second['cash']['revenue'], Decimal('1000.00'))
