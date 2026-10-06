import json
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

from trips.models import CARD, CASH, Trip

ALMATY = ZoneInfo('Asia/Almaty')
TWOPLACES = Decimal('0.01')
PAYMENTS = {CASH, CARD}


class TripError(Exception):
    def __init__(self, errors):
        self.errors = errors


class TripConflict(Exception):
    pass


def money(value):
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def parse_day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def day_bounds(day):
    start = datetime.combine(day, time.min, tzinfo=ALMATY)
    end = datetime.combine(day, time.max, tzinfo=ALMATY)
    return start, end


def trips_for_day(day):
    start, end = day_bounds(day)
    return Trip.objects.filter(start__gte=start, start__lte=end).order_by('start', 'trip_id')


def trip_days():
    rows = (
        Trip.objects.annotate(day=TruncDate('start', tzinfo=ALMATY))
        .values_list('day', flat=True)
        .distinct()
        .order_by('day')
    )
    return [day.isoformat() for day in rows]


def build_summary(trips):
    row = trips.aggregate(
        trip_count=Count('pk'),
        revenue=Sum('amount'),
        commission_sum=Sum('commission'),
        cash_count=Count('pk', filter=Q(payment=CASH)),
        cash_revenue=Sum('amount', filter=Q(payment=CASH)),
        card_count=Count('pk', filter=Q(payment=CARD)),
        card_revenue=Sum('amount', filter=Q(payment=CARD)),
    )
    revenue = money(row['revenue'])
    commission = money(row['commission_sum'])
    return {
        'trip_count': row['trip_count'],
        'revenue': revenue,
        'commission': commission,
        'net': revenue - commission,
        'cash': {
            'trip_count': row['cash_count'],
            'revenue': money(row['cash_revenue']),
        },
        'card': {
            'trip_count': row['card_count'],
            'revenue': money(row['card_revenue']),
        },
    }


def summary_payload(summary):
    def pack(block):
        return {
            'trip_count': block['trip_count'],
            'revenue': str(block['revenue']),
        }

    return {
        'trip_count': summary['trip_count'],
        'revenue': str(summary['revenue']),
        'commission': str(summary['commission']),
        'net': str(summary['net']),
        'cash': pack(summary['cash']),
        'card': pack(summary['card']),
    }


def read_amount(data, field, errors, greater_than_zero):
    raw = data.get(field)
    if isinstance(raw, bool) or raw is None or raw == '':
        errors[field] = 'Укажите число'
        return None
    if isinstance(raw, str):
        raw = raw.strip().replace(' ', '').replace(',', '.')
        if raw == '':
            errors[field] = 'Укажите число'
            return None
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        errors[field] = 'Укажите число'
        return None
    if money(value) != value:
        errors[field] = 'Не больше двух знаков после запятой'
        return None
    if greater_than_zero and value <= 0:
        errors[field] = 'Сумма должна быть больше 0'
        return None
    if not greater_than_zero and value < 0:
        errors[field] = 'Комиссия не может быть отрицательной'
        return None
    return money(value)


def read_moment(data, field, errors):
    raw = data.get(field)
    if not isinstance(raw, str) or not raw.strip():
        errors[field] = 'Укажите время'
        return None
    try:
        parsed = datetime.fromisoformat(raw.strip())
    except ValueError:
        errors[field] = 'Время должно быть в формате ISO 8601'
        return None
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        errors[field] = 'Укажите время с часовым поясом'
        return None
    return parsed


def parse_trip_payload(data):
    if not isinstance(data, dict):
        raise TripError({'detail': 'Тело запроса должно быть объектом JSON'})
    errors = {}
    trip_id = str(data.get('id') or '').strip()
    if not trip_id:
        errors['id'] = 'Укажите id поездки'
    elif len(trip_id) > 64:
        errors['id'] = 'id не длиннее 64 символов'
    amount = read_amount(data, 'amount', errors, True)
    commission = read_amount(data, 'commission', errors, False)
    start = read_moment(data, 'start', errors)
    end = read_moment(data, 'end', errors)
    payment = str(data.get('payment') or '').strip().lower()
    if payment not in PAYMENTS:
        errors['payment'] = 'Способ оплаты: cash или card'
    if start is not None and end is not None and end <= start:
        errors['end'] = 'Окончание должно быть позже начала'
    if errors:
        raise TripError(errors)
    return {
        'trip_id': trip_id,
        'start': start,
        'end': end,
        'amount': amount,
        'payment': payment,
        'commission': commission,
    }


def same_trip(trip, cleaned):
    return (
        trip.start == cleaned['start']
        and trip.end == cleaned['end']
        and trip.amount == cleaned['amount']
        and trip.payment == cleaned['payment']
        and trip.commission == cleaned['commission']
    )


def create_trip(data):
    cleaned = parse_trip_payload(data)
    try:
        with transaction.atomic():
            trip = Trip.objects.create(
                trip_id=cleaned['trip_id'],
                start=cleaned['start'],
                end=cleaned['end'],
                amount=cleaned['amount'],
                payment=cleaned['payment'],
                commission=cleaned['commission'],
            )
    except IntegrityError:
        trip = Trip.objects.get(trip_id=cleaned['trip_id'])
        if not same_trip(trip, cleaned):
            raise TripConflict()
        return trip, False
    return trip, True


def load_seed(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    created_count = 0
    for item in payload:
        trip, created = create_trip(item)
        if created:
            created_count += 1
    return created_count
