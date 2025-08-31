from django.core.management.base import BaseCommand
from voice_translator.models import Language


class Command(BaseCommand):
    help = 'Populate the database with initial languages'

    def handle(self, *args, **options):
        languages = [
            {'code': 'en', 'name': 'English', 'flag': '🇺🇸'},
            {'code': 'es', 'name': 'Spanish', 'flag': '🇪🇸'},
            {'code': 'fr', 'name': 'French', 'flag': '🇫🇷'},
            {'code': 'de', 'name': 'German', 'flag': '🇩🇪'},
            {'code': 'it', 'name': 'Italian', 'flag': '🇮🇹'},
            {'code': 'pt', 'name': 'Portuguese', 'flag': '🇵🇹'},
            {'code': 'ru', 'name': 'Russian', 'flag': '🇷🇺'},
            {'code': 'ja', 'name': 'Japanese', 'flag': '🇯🇵'},
            {'code': 'ko', 'name': 'Korean', 'flag': '🇰🇷'},
            {'code': 'zh', 'name': 'Chinese', 'flag': '🇨🇳'},
        ]

        for lang_data in languages:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults={
                    'name': lang_data['name'],
                    'flag': lang_data['flag']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created language: {language.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Language already exists: {language.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated languages!')
        )
