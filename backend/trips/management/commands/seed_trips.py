from pathlib import Path

from django.core.management.base import BaseCommand

from trips.services import load_seed


class Command(BaseCommand):
    help = 'Загружает пример поездок. Повторный запуск не создаёт дубли.'

    def handle(self, *args, **options):
        path = Path(__file__).resolve().parents[2] / 'data' / 'trips.json'
        created_count = load_seed(path)
        self.stdout.write(self.style.SUCCESS(f'Создано поездок: {created_count}'))
