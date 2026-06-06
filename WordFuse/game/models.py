from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_words = models.IntegerField(default=0)
    best_score = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    avg_wpm = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class GameSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.score} pts"
    
class Turn(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    syllable = models.CharField(max_length=20)
    word_submitted = models.CharField(max_length=100, blank=True)
    is_valid = models.BooleanField(default=False)
    time_taken_ms = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.syllable} -> {self.word_submitted}"
    

class WordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.CharField(max_length=100)

    class Meta:
        unique_together = ("user", "word")

    def __str__(self):
        return f"{self.user.username}: {self.word}"
    

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    condition_key = models.CharField(max_length=50)
    threshold = models.IntegerField()

    def __str__(self):
        return self.name
    

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "achievement")

        def __str__(self):
            return f"{self.user.username} - {self.achievement.name}"