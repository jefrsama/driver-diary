from django.test import TestCase
from rest_framework.test import APIClient

from trips.models import Trip


EXAMPLE = {
    'id': 't1',
    'start': '2026-10-01T08:10:00+05:00',
    'end': '2026-10-01T08:32:00+05:00',
    'amount': 2400,
    'payment': 'card',
    'commission': 360,
}


class ApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_day_summary_matches_example(self):
        second = {
            'id': 't2',
            'start': '2026-10-01T09:05:00+05:00',
            'end': '2026-10-01T09:20:00+05:00',
            'amount': 1500,
            'payment': 'cash',
            'commission': 225,
        }
        self.assertEqual(self.client.post('/api/trips/', EXAMPLE, format='json').status_code, 201)
        self.assertEqual(self.client.post('/api/trips/', second, format='json').status_code, 201)
        response = self.client.get('/api/days/2026-10-01/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['summary'], {
            'trip_count': 2,
            'revenue': '3900.00',
            'commission': '585.00',
            'net': '3315.00',
            'cash': {'trip_count': 1, 'revenue': '1500.00'},
            'card': {'trip_count': 1, 'revenue': '2400.00'},
        })
        self.assertEqual([item['id'] for item in body['trips']], ['t1', 't2'])

    def test_repeat_post_does_not_duplicate(self):
        first = self.client.post('/api/trips/', EXAMPLE, format='json')
        second = self.client.post('/api/trips/', EXAMPLE, format='json')
        self.assertEqual(first.status_code, 201)
        self.assertTrue(first.json()['created'])
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.json()['created'])
        self.assertEqual(Trip.objects.count(), 1)
        day = self.client.get('/api/days/2026-10-01/').json()
        self.assertEqual(day['summary']['trip_count'], 1)
        self.assertEqual(day['summary']['revenue'], '2400.00')

    def test_same_id_with_other_amount_is_conflict(self):
        self.client.post('/api/trips/', EXAMPLE, format='json')
        other = dict(EXAMPLE, amount=999)
        response = self.client.post('/api/trips/', other, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Trip.objects.get().amount, 2400)

    def test_comma_amount_is_accepted(self):
        payload = dict(EXAMPLE, id='comma', amount='2 400,50', commission='360,25')
        response = self.client.post('/api/trips/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['trip']['amount'], '2400.50')
        self.assertEqual(response.json()['trip']['commission'], '360.25')

    def test_amount_must_be_positive(self):
        response = self.client.post('/api/trips/', dict(EXAMPLE, amount=0), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('amount', response.json()['errors'])
        self.assertEqual(Trip.objects.count(), 0)

    def test_end_must_be_after_start(self):
        same_time = dict(EXAMPLE, end=EXAMPLE['start'])
        earlier = dict(EXAMPLE, end='2026-10-01T08:00:00+05:00')
        self.assertEqual(self.client.post('/api/trips/', same_time, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/trips/', earlier, format='json').status_code, 400)
        self.assertEqual(Trip.objects.count(), 0)

    def test_late_evening_stays_on_local_day(self):
        payload = dict(
            EXAMPLE,
            id='night',
            start='2026-10-02T01:30:00+05:00',
            end='2026-10-02T01:50:00+05:00',
        )
        self.assertEqual(self.client.post('/api/trips/', payload, format='json').status_code, 201)
        october_first = self.client.get('/api/days/2026-10-01/').json()
        october_second = self.client.get('/api/days/2026-10-02/').json()
        self.assertEqual(october_first['trips'], [])
        self.assertEqual(october_second['trips'][0]['id'], 'night')
        self.assertEqual(self.client.get('/api/days/').json()['dates'], ['2026-10-02'])
