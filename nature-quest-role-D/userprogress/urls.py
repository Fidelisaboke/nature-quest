from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.UserProfileViewSet, basename='userprofile')
router.register(r'badges', views.BadgeViewSet)
router.register(r'levels', views.LevelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-progress/', views.ProgressUpdateAPIView.as_view(), name='update-progress'),
    path('leaderboard/', views.LeaderboardAPIView.as_view(), name='leaderboard'),
    path('stats/', views.UserStatsAPIView.as_view(), name='user-stats'),
    path('stats/<int:user_id>/', views.UserStatsAPIView.as_view(), name='user-stats-by-id'),
    path('points-history/', views.PointsHistoryAPIView.as_view(), name='points-history'),
]
