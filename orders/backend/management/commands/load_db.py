# backend/management/commands/load_db.py

from django.core.management.base import BaseCommand, CommandError
from backend.utils import load_data # Импортируем нашу функцию

class Command(BaseCommand):
    help = 'Загружает данные из YAML-файла в базу данных.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к YAML-файлу для импорта')

    def handle(self, *args, **options):
        file_path = options['file_path']

        result = load_data(file_path)

        if result['Status']:
            self.stdout.write(
                self.style.SUCCESS(result['Message'])
            )
        else:
            raise CommandError(result['Error'])
