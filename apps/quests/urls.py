from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r"challenges", views.ChallengeViewSet, basename="challenge")
router.register(r"attempts", views.ChallengeAttemptViewSet, basename="challengeattempt")
router.register(r"verification", views.VerificationViewSet, basename="verification")
router.register(
    r"admin/challenges", views.AdminChallengeViewSet, basename="admin-challenge"
)
router.register(
    r"admin/fraud-detection", views.AdminFraudDetectionViewSet, basename="admin-fraud"
)

urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Additional challenge verification endpoints
    path(
        "challenges/<int:challenge_id>/submit/",
        views.ChallengeAttemptViewSet.as_view({"post": "create"}),
        name="submit-challenge",
    ),
    path(
        "attempts/<int:pk>/resubmit/",
        views.ChallengeAttemptViewSet.as_view({"post": "resubmit"}),
        name="resubmit-challenge",
    ),
    # Verification details endpoints
    path(
        "verification/photo-analysis/",
        views.VerificationViewSet.as_view({"get": "photo_analysis"}),
        name="photo-analysis",
    ),
    path(
        "verification/location-verification/",
        views.VerificationViewSet.as_view({"get": "location_verification"}),
        name="location-verification",
    ),
    path(
        "verification/metrics/",
        views.VerificationViewSet.as_view({"get": "metrics"}),
        name="verification-metrics",
    ),
    # User progress endpoint
    path(
        "challenges/my-progress/",
        views.ChallengeViewSet.as_view({"get": "my_progress"}),
        name="challenge-progress",
    ),
    # Admin endpoints
    path(
        "admin/challenges/statistics/",
        views.AdminChallengeViewSet.as_view({"get": "statistics"}),
        name="admin-challenge-stats",
    ),
    path(
        "admin/fraud-detection/<int:pk>/review/",
        views.AdminFraudDetectionViewSet.as_view({"post": "review_submission"}),
        name="admin-fraud-review",
    ),
]
