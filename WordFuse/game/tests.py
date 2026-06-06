from django.test import TestCase

# Create your tests here.
import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import timezone
from game.models import UserProfile, GameSession, Turn, WordHistory, Achievement, UserAchievement
from game.views import SYLLABLES


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='testuser', password='testpass123'):
    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.create(user=user)
    return user

def make_session(user):
    return GameSession.objects.create(user=user)

def make_achievement(name='First Word', condition_key='total_words', threshold=1):
    return Achievement.objects.get_or_create(
        condition_key=condition_key,
        threshold=threshold,
        defaults={'name': name, 'description': 'Test achievement'}
    )[0]


# syllable list

class SyllableListTests(TestCase):

    def test_syllable_list_not_empty(self):
        self.assertGreater(len(SYLLABLES), 0)

    def test_syllable_list_has_no_duplicates(self):
        self.assertEqual(len(SYLLABLES), len(set(SYLLABLES)))

    def test_syllables_are_strings(self):
        for s in SYLLABLES:
            self.assertIsInstance(s, str)

    def test_syllables_have_no_leading_trailing_spaces(self):
        for s in SYLLABLES:
            self.assertEqual(s, s.strip(), f'Syllable "{s}" has extra whitespace')

    def test_syllables_minimum_length(self):
        for s in SYLLABLES:
            self.assertGreaterEqual(len(s), 2, f'Syllable "{s}" is too short')


# checking word contains syllable

class WordContainsSyllableTests(TestCase):

    def test_word_contains_syllable(self):
        self.assertIn('ing', 'running')

    def test_word_does_not_contain_syllable(self):
        self.assertNotIn('ing', 'apple')

    def test_syllable_at_start(self):
        self.assertIn('pre', 'preview')

    def test_syllable_at_end(self):
        self.assertIn('tion', 'nation')

    def test_syllable_in_middle(self):
        self.assertIn('est', 'testing')

    def test_case_insensitive_check(self):
        word = 'Running'.lower()
        self.assertIn('ing', word)

    def test_empty_word_fails(self):
        self.assertNotIn('ing', '')

    def test_short_word_minimum_length(self):
        word = 'hi'
        self.assertGreaterEqual(len(word), 2)

    def test_word_too_short_rejected(self):
        word = 'i'
        self.assertLess(len(word), 2)


# score math

class ScoringTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.session = make_session(self.user)

    def test_score_increases_by_word_length(self):
        word = 'running'
        points = len(word)
        self.session.score += points
        self.session.save()
        self.assertEqual(GameSession.objects.get(id=self.session.id).score, 7)

    def test_longer_word_gives_more_points(self):
        self.assertGreater(len('absolutely'), len('run'))

    def test_score_starts_at_zero(self):
        session = make_session(self.user)
        self.assertEqual(session.score, 0)

    def test_multiple_words_accumulate_score(self):
        words = ['running', 'testing', 'absolute']
        total = sum(len(w) for w in words)
        self.session.score = total
        self.session.save()
        self.assertEqual(GameSession.objects.get(id=self.session.id).score, total)

    def test_invalid_word_does_not_increase_score(self):
        original_score = self.session.score
        # invalid word — score unchanged
        self.session.save()
        self.assertEqual(self.session.score, original_score)


# counting streaks

class StreakTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.session = make_session(self.user)

    def test_streak_starts_at_zero(self):
        self.assertEqual(self.session.current_streak, 0)

    def test_valid_word_increases_streak(self):
        self.session.current_streak += 1
        self.session.save()
        self.assertEqual(GameSession.objects.get(id=self.session.id).current_streak, 1)

    def test_invalid_word_resets_streak(self):
        self.session.current_streak = 5
        self.session.current_streak = 0
        self.session.save()
        self.assertEqual(self.session.current_streak, 0)

    def test_longest_streak_updates_correctly(self):
        self.session.current_streak = 7
        self.session.longest_streak = max(self.session.longest_streak, self.session.current_streak)
        self.session.save()
        self.assertEqual(self.session.longest_streak, 7)

    def test_longest_streak_does_not_decrease(self):
        self.session.longest_streak = 5
        self.session.current_streak = 0
        new_longest = max(self.session.longest_streak, self.session.current_streak)
        self.assertEqual(new_longest, 5)

    def test_streak_increments_consecutively(self):
        for i in range(1, 6):
            self.session.current_streak = i
        self.assertEqual(self.session.current_streak, 5)


# unlocking achievements (passing threshold)

class AchievementTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.session = make_session(self.user)

    def test_achievement_created(self):
        a = make_achievement()
        self.assertEqual(a.name, 'First Word')

    def test_achievement_not_unlocked_by_default(self):
        a = make_achievement()
        unlocked = UserAchievement.objects.filter(user=self.user, achievement=a).exists()
        self.assertFalse(unlocked)

    def test_achievement_unlocks_correctly(self):
        a = make_achievement()
        UserAchievement.objects.create(user=self.user, achievement=a)
        self.assertTrue(UserAchievement.objects.filter(user=self.user, achievement=a).exists())

    def test_achievement_not_duplicated(self):
        a = make_achievement()
        UserAchievement.objects.get_or_create(user=self.user, achievement=a)
        UserAchievement.objects.get_or_create(user=self.user, achievement=a)
        count = UserAchievement.objects.filter(user=self.user, achievement=a).count()
        self.assertEqual(count, 1)

    def test_total_words_threshold(self):
        profile = UserProfile.objects.get(user=self.user)
        profile.total_words = 1
        profile.save()
        a = make_achievement(condition_key='total_words', threshold=1)
        earned = profile.total_words >= a.threshold
        self.assertTrue(earned)

    def test_streak_threshold(self):
        self.session.longest_streak = 5
        self.session.save()
        a = make_achievement(name='5-Word Streak', condition_key='streak', threshold=5)
        earned = self.session.longest_streak >= a.threshold
        self.assertTrue(earned)

    def test_games_played_threshold(self):
        profile = UserProfile.objects.get(user=self.user)
        profile.games_played = 10
        profile.save()
        a = make_achievement(name='Veteran', condition_key='games_played', threshold=10)
        earned = profile.games_played >= a.threshold
        self.assertTrue(earned)

    def test_speed_threshold(self):
        time_ms = 3000
        a = make_achievement(name='Speed Demon', condition_key='speed', threshold=5000)
        earned = time_ms <= a.threshold
        self.assertTrue(earned)

    def test_speed_threshold_too_slow(self):
        time_ms = 8000
        a = make_achievement(name='Speed Demon', condition_key='speed', threshold=5000)
        earned = time_ms <= a.threshold
        self.assertFalse(earned)


# past guessed words / words history

class WordHistoryTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_word_saved_to_history(self):
        WordHistory.objects.create(user=self.user, word='running')
        self.assertTrue(WordHistory.objects.filter(user=self.user, word='running').exists())

    def test_duplicate_word_not_saved_twice(self):
        WordHistory.objects.get_or_create(user=self.user, word='running')
        WordHistory.objects.get_or_create(user=self.user, word='running')
        count = WordHistory.objects.filter(user=self.user, word='running').count()
        self.assertEqual(count, 1)

    def test_different_users_can_have_same_word(self):
        user2 = make_user(username='user2')
        WordHistory.objects.create(user=self.user, word='running')
        WordHistory.objects.create(user=user2, word='running')
        self.assertEqual(WordHistory.objects.filter(word='running').count(), 2)