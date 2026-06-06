from django.core.management.base import BaseCommand
from game.models import Achievement

class Command(BaseCommand):
    help = 'Seed initial achievements'

    def handle(self, *args, **kwargs):
        achievements = [
            {
                'name': 'First Word',
                'description': 'Submit your first valid word.',
                'condition_key': 'total_words',
                'threshold': 1,
            },
            {
                'name': '5-Word Streak',
                'description': 'Get a 5-word streak in a single game.',
                'condition_key': 'streak',
                'threshold': 5,
            },
            {
                'name': '10-Word Streak',
                'description': 'Get a 10-word streak in a single game.',
                'condition_key': 'streak',
                'threshold': 10,
            },
            {
                'name': 'Speed Demon',
                'description': 'Submit a valid word in under 5 seconds.',
                'condition_key': 'speed',
                'threshold': 5000,
            },
            {
                'name': 'Veteran',
                'description': 'Play 10 games.',
                'condition_key': 'games_played',
                'threshold': 10,
            },
            {
                'name': 'Perfect Game',
                'description': 'Finish a game without losing a single life.',
                'condition_key': 'perfect_game',
                'threshold': 1,
            },
        ]

        for a in achievements:
            obj, created = Achievement.objects.get_or_create(
                condition_key=a['condition_key'],
                threshold=a['threshold'],
                defaults={
                    'name': a['name'],
                    'description': a['description'],
                },
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"{status}: {a['name']}")
            