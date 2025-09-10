from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestViewSet

router = DefaultRouter()
router.register(r'quests', QuestViewSet)

urlpatterns = [
    path('api/v1/quests/', include(router.urls)),
    path('api/v1/quests/<int:pk>/find-nearby/', QuestViewSet.as_view({'get': 'find_quest_nearby'}), name='find_quest_nearby'),
    path('api/v1/quests/<int:pk>/start/', QuestViewSet.as_view({'post': 'start_quest'}), name='start_quest'),
] + router.urls