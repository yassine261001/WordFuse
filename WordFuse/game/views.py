import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from .models import UserProfile
import random
import requests
from django.utils import timezone
from .models import UserProfile, GameSession, Turn, WordHistory, Achievement, UserAchievement

def index(request):
    return render(request, 'game/game.html')

@ensure_csrf_cookie
@require_GET
def auth_status(request):
    if request.user.is_authenticated:
        return JsonResponse({'logged_in': True, 'username': request.user.username})
    return JsonResponse({'logged_in': False})

@require_POST
def register(request):
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return JsonResponse({'error': 'Username and password required.'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already taken.'}, status=400)

    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.create(user=user)
    login(request, user)
    return JsonResponse({'success': True, 'username': user.username})

@require_POST
def user_login(request):
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'error': 'Invalid username or password.'}, status=400)

    login(request, user)
    return JsonResponse({'success': True, 'username': user.username})


@require_POST
def user_logout(request):
    logout(request)
    return JsonResponse({'success': True})

SYLLABLES = list(set([
    # Prefixes
    'pre', 'pro', 'con', 'com', 'per', 'dis', 'mis', 'non', 'out',
    'over', 'under', 'inter', 'super', 'sub', 'un', 're', 'in',
    'ex', 'en', 'em', 'de', 'be', 'fore', 'mid', 'semi', 'anti',

    # Suffixes
    'ing', 'tion', 'ness', 'ment', 'ful', 'less', 'able', 'ible',
    'est', 'ent', 'ant', 'ish', 'ive', 'ous', 'ary', 'ery', 'ory',
    'age', 'ure', 'ture', 'sion', 'ance', 'ence', 'ward', 'wise',
    'ling', 'let', 'ette',

    # -at / -an / -ar
    'act', 'ack', 'ank', 'ang', 'amp', 'and', 'ant', 'ark',
    'arm', 'art', 'ash', 'ask', 'atch', 'ave', 'awn', 'axe',
    'air', 'aim', 'aid', 'ail', 'ain', 'ake', 'ale', 'ame',
    'ane', 'ape', 'are', 'ate',

    # -ea / -ee
    'each', 'ead', 'eak', 'eal', 'eam', 'ean', 'eap', 'ear',
    'eat', 'eck', 'eed', 'eek', 'eel', 'een', 'eep', 'eer',
    'ell', 'elp', 'elt', 'end', 'erm', 'ern',

    # -i
    'ice', 'ick', 'ide', 'ife', 'ift', 'ile', 'ilk', 'ill',
    'ilt', 'ime', 'imp', 'ine', 'ink', 'int', 'ire', 'irk',
    'ist', 'ite',

    # -o
    'ock', 'ode', 'oke', 'old', 'ole', 'olt', 'one', 'ong',
    'ood', 'ook', 'ool', 'oom', 'oon', 'oop', 'oot', 'ope',
    'ore', 'ork', 'orm', 'orn', 'ort', 'ose', 'ost', 'ote',
    'oud', 'ound', 'our', 'ove', 'own',

    # -u
    'uck', 'uff', 'ull', 'umb', 'ump', 'und', 'ung', 'unk',
    'unt', 'urn', 'urt', 'ush', 'ust', 'ute',

    'ight', 'ough', 'tion', 'hard', 'more', 'ever', 'over', 'some', 'stor', 'stun', 'will'
]))

def is_real_word(word):
    try:
        response = requests.get(
            f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}',
            timeout=5
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


@require_POST
def start_game(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    session = GameSession.objects.create(user=request.user)
    syllable = random.choice(SYLLABLES)

    Turn.objects.create(session=session, syllable=syllable)

    return JsonResponse({
        'session_id': session.id,
        'syllable': syllable,
    })


@require_POST
def submit_word(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    data = json.loads(request.body)
    session_id = data.get('session_id')
    word = data.get('word', '').strip().lower()

    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
    except GameSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found.'}, status=404)

    current_turn = Turn.objects.filter(session=session).last()
    syllable = current_turn.syllable

    # Already used check — must come after session and current_turn are defined
    already_used = Turn.objects.filter(
        session=session,
        word_submitted=word,
        is_valid=True
    ).exists()

    if already_used:
        return JsonResponse({
            'already_used': True,
            'syllable': syllable,
        })

    word_valid = (
        syllable in word and
        len(word) >= 2 and
        is_real_word(word)
    )

    current_turn.word_submitted = word
    current_turn.is_valid = word_valid
    current_turn.save()

    if word_valid:
        points = len(word)
        session.score += points
        session.current_streak += 1
        session.longest_streak = max(session.longest_streak, session.current_streak)
        session.save()

        WordHistory.objects.get_or_create(user=request.user, word=word)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.total_words += 1
        profile.save()
        newly_unlocked = _check_achievements(request.user, session, turn_time_ms=data.get('time_ms'))

        syllable = random.choice(SYLLABLES)
        Turn.objects.create(session=session, syllable=syllable)

        return JsonResponse({
            'valid': True,
            'points': points,
            'score': session.score,
            'syllable': syllable,
            'game_over': False,
            'lives': data.get('lives', 3),
            'achievements': newly_unlocked,
        })
    
    else:
        session.current_streak = 0
        session.save()

        lives_remaining = data.get('lives', 3) - 1

        game_over = lives_remaining <= 0

        if game_over:
            session.ended_at = timezone.now()
            session.save()
            newly_unlocked = _update_profile(request.user, session)
        else:
            newly_unlocked = []

        syllable = random.choice(SYLLABLES)

        if not game_over:
            Turn.objects.create(session=session, syllable=syllable)

        return JsonResponse({
            'valid': False,
            'score': session.score,
            'syllable': syllable,
            'game_over': game_over,
            'lives': lives_remaining,
            'achievements': newly_unlocked
        })


@require_POST
def game_timeout(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    data = json.loads(request.body)
    session_id = data.get('session_id')

    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
    except GameSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found.'}, status=404)

    session.current_streak = 0
    session.save()

    lives_remaining = data.get('lives', 3) - 1

    game_over = lives_remaining <= 0

    if game_over:
        session.ended_at = timezone.now()
        session.save()
        newly_unlocked = _update_profile(request.user, session)
    else:
        newly_unlocked = []

    syllable = random.choice(SYLLABLES)

    if not game_over:
        Turn.objects.create(session=session, syllable=syllable)

    return JsonResponse({
        'lives': lives_remaining,
        'syllable': syllable,
        'game_over': game_over,
        'score': session.score,
        'achievements': newly_unlocked
    })


@require_GET
def leaderboard(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    profiles = UserProfile.objects.select_related('user').order_by('-best_score')[:10]
    data = [
        {'username': p.user.username, 'best_score': p.best_score}
        for p in profiles
    ]
    return JsonResponse({'leaderboard': data})


def _update_profile(user, session):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.games_played += 1
    profile.total_words += Turn.objects.filter(session=session, is_valid=True).count()
    profile.best_score = max(profile.best_score, session.score)
    profile.best_streak = max(profile.best_streak, session.longest_streak)
    profile.save()
    return _check_achievements(user, session)

def _check_achievements(user, session, turn_time_ms=None):
    profile = UserProfile.objects.get(user=user)
    all_achievements = Achievement.objects.all()
    unlocked = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)

    newly_unlocked = []

    for achievement in all_achievements:
        if achievement.id in unlocked:
            continue

        earned = False

        if achievement.condition_key == 'total_words':
            earned = profile.total_words >= achievement.threshold

        elif achievement.condition_key == 'streak':
            earned = session.longest_streak >= achievement.threshold

        elif achievement.condition_key == 'games_played':
            earned = profile.games_played >= achievement.threshold

        elif achievement.condition_key == 'speed' and turn_time_ms is not None:
            earned = turn_time_ms <= achievement.threshold

        elif achievement.condition_key == 'perfect_game':
            turns = Turn.objects.filter(session=session)
            lives_lost = turns.filter(is_valid=False).count()
            timeouts = session.turn_set.count() - turns.filter(is_valid=True).count()
            earned = (lives_lost == 0 and session.ended_at is not None)

        if earned:
            UserAchievement.objects.create(user=user, achievement=achievement)
            newly_unlocked.append(achievement.name)

    return newly_unlocked