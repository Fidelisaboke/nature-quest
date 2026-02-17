from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestViewSet, ChallengeViewSet, GamificationViewSet

router = DefaultRouter()
router.register(r'quests', QuestViewSet, basename='quest')
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'gamification', GamificationViewSet, basename='gamification')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    # Quest endpoints
    path('api/v1/quests/<int:pk>/find-nearby/', QuestViewSet.as_view({'get': 'find_quest_nearby'}), name='find_quest_nearby'),
    path('api/v1/quests/<int:pk>/start/', QuestViewSet.as_view({'post': 'start_quest'}), name='start_quest'),
    path('api/v1/quests/<int:pk>/complete/', QuestViewSet.as_view({'post': 'complete_quest'}), name='complete_quest'),
    path('api/v1/quests/<int:pk>/abandon/', QuestViewSet.as_view({'post': 'abandon_quest'}), name='abandon_quest'),
    # New location-based endpoints
    path('api/v1/quests/discover/', QuestViewSet.as_view({'get': 'discover'}), name='quest_discover'),
    path('api/v1/quests/<int:pk>/validate-location/', QuestViewSet.as_view({'post': 'validate_location'}), name='quest_validate_location'),
    # Challenge endpoints
    path('api/v1/challenges/<int:pk>/start/', ChallengeViewSet.as_view({'post': 'start_challenge'}), name='start_challenge'),
    path('api/v1/challenges/<int:pk>/complete/', ChallengeViewSet.as_view({'post': 'complete_challenge'}), name='complete_challenge'),
    path('api/v1/challenges/<int:pk>/abandon/', ChallengeViewSet.as_view({'post': 'abandon_challenge'}), name='abandon_challenge'),
    # Gamification endpoints
    path('api/v1/gamification/profile/', GamificationViewSet.as_view({'get': 'profile'}), name='gamification_profile'),
    path('api/v1/gamification/badges/', GamificationViewSet.as_view({'get': 'badges'}), name='gamification_badges'),
    path('api/v1/gamification/leaderboards/', GamificationViewSet.as_view({'get': 'leaderboards'}), name='gamification_leaderboards'),
    path('api/v1/gamification/environmental-impact/', GamificationViewSet.as_view({'get': 'environmental_impact'}), name='gamification_environmental_impact'),
]