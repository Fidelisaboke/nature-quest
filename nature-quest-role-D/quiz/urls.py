from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'quizzes', views.QuizViewSet, basename='quiz')
router.register(r'attempts', views.QuizAttemptViewSet, basename='quizattempt')
router.register(r'question-bank', views.QuestionBankViewSet, basename='questionbank')

urlpatterns = [
    path('', include(router.urls)),
    path('generate/', views.QuizGenerationAPIView.as_view(), name='generate-quiz'),
    path('stats/', views.QuizStatsAPIView.as_view(), name='quiz-stats'),
    path('stats/<int:user_id>/', views.QuizStatsAPIView.as_view(), name='quiz-stats-by-id'),
    path('metrics/', views.QuizMetricsAPIView.as_view(), name='quiz-metrics'),
]
