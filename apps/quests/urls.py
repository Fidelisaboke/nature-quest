from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestViewSet, ChallengeViewSet

router = DefaultRouter()
router.register(r'quests', QuestViewSet)
router.register(r'challenges', ChallengeViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/quests/<int:pk>/find-nearby/', QuestViewSet.as_view({'get': 'find_quest_nearby'}), name='find_quest_nearby'),
    path('api/v1/quests/<int:pk>/start/', QuestViewSet.as_view({'post': 'start_quest'}), name='start_quest'),
    path('api/v1/quests/<int:pk>/complete/', QuestViewSet.as_view({'post': 'complete_quest'}), name='complete_quest'),
    path('api/v1/quests/<int:pk>/abandon/', QuestViewSet.as_view({'post': 'abandon_quest'}), name='abandon_quest'),
    
]