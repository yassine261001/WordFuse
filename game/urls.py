from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth/status/', views.auth_status, name='auth_status'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.user_login, name='login'),
    path('auth/logout/', views.user_logout, name='logout'),
    path('game/start/', views.start_game, name='start_game'),
    path('game/submit/', views.submit_word, name='submit_word'),
    path('game/timeout/', views.game_timeout, name='game_timeout'),
    path('game/leaderboard/', views.leaderboard, name='leaderboard'),
]