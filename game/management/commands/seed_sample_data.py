from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from game.models import UserProfile, GameSession, Turn, WordHistory, Achievement, UserAchievement


class Command(BaseCommand):
    help = 'Seed sample users, sessions and achievements'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding sample data...')

        # Sample users
        users_data = [
            {'username': 'alex99', 'password': 'demo1234'},
            {'username': 'wordmaster', 'password': 'demo1234'},
            {'username': 'syllable_king', 'password': 'demo1234'},
            {'username': 'quicktyper', 'password': 'demo1234'},
        ]

        users = []
        for u in users_data:
            if User.objects.filter(username=u['username']).exists():
                user = User.objects.get(username=u['username'])
                self.stdout.write(f'Already exists: {u["username"]}')
            else:
                user = User.objects.create_user(
                    username=u['username'],
                    password=u['password']
                )
                self.stdout.write(f'Created user: {u["username"]}')
            UserProfile.objects.get_or_create(user=user)
            users.append(user)

        # Sample words per syllable
        word_bank = {
            'ing': ['singing', 'running', 'jumping', 'winging', 'bringing'],
            'est': ['fastest', 'biggest', 'strongest', 'greatest', 'modest'],
            'tion': ['nation', 'station', 'motion', 'section', 'mention'],
            'ack': ['track', 'black', 'attack', 'backpack', 'stack'],
            'ell': ['spell', 'shell', 'yell', 'dwell', 'stellar'],
            'ound': ['sound', 'ground', 'around', 'found', 'hound'],
            'ight': ['night', 'flight', 'bright', 'slight', 'knight'],
            'and': ['stand', 'grand', 'band', 'land', 'expand'],
            'ore': ['explore', 'store', 'core', 'shore', 'adore'],
            'ive': ['drive', 'alive', 'active', 'live', 'strive'],
        }
        syllables = list(word_bank.keys())

        achievements = list(Achievement.objects.all())

        # Create sessions for each user
        for user in users:
            profile = UserProfile.objects.get(user=user)
            num_sessions = random.randint(3, 6)

            for s in range(num_sessions):
                started = timezone.now() - timedelta(days=random.randint(1, 14))
                session = GameSession.objects.create(
                    user=user,
                    started_at=started,
                    ended_at=started + timedelta(minutes=random.randint(2, 8)),
                )

                score = 0
                streak = 0
                longest_streak = 0
                num_turns = random.randint(5, 15)

                for t in range(num_turns):
                    syllable = random.choice(syllables)
                    words = word_bank[syllable]
                    word = random.choice(words)
                    is_valid = random.random() > 0.2

                    Turn.objects.create(
                        session=session,
                        syllable=syllable,
                        word_submitted=word,
                        is_valid=is_valid,
                        time_taken_ms=random.randint(1500, 12000),
                    )

                    if is_valid:
                        score += len(word)
                        streak += 1
                        longest_streak = max(longest_streak, streak)
                        WordHistory.objects.get_or_create(user=user, word=word)
                    else:
                        streak = 0

                session.score = score
                session.longest_streak = longest_streak
                session.save()

                profile.games_played += 1
                profile.total_words += Turn.objects.filter(session=session, is_valid=True).count()
                profile.best_score = max(profile.best_score, score)
                profile.best_streak = max(profile.best_streak, longest_streak)

            profile.save()

            # Unlock 2-3 random achievements per user
            for achievement in random.sample(achievements, min(3, len(achievements))):
                UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'unlocked_at': timezone.now() - timedelta(days=random.randint(1, 10))}
                )

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully.'))
        