from django.contrib import admin
from django.contrib import admin
from .models import UserProfile, GameSession, Turn, WordHistory, Achievement, UserAchievement

admin.site.register(UserProfile)
admin.site.register(GameSession)
admin.site.register(Turn)
admin.site.register(WordHistory)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
