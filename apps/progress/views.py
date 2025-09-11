from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import UserProfile, Badge, Level, UserBadge, PointsTransaction
from .serializers import (
    UserProfileSerializer,
    BadgeSerializer,
    LevelSerializer,
    UserBadgeSerializer,
    PointsTransactionSerializer,
    UserStatsSerializer,
    ProgressUpdateSerializer,
)
from .services import ProgressService
import logging

logger = logging.getLogger(__name__)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles"""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create user profile for the authenticated user"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    @action(detail=False, methods=["get"])
    def my_profile(self, request):
        """Get current user's profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def update_interests(self, request):
        """Update user's interests"""
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing available badges"""

    queryset = Badge.objects.all().order_by("points_required")
    serializer_class = BadgeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def my_badges(self, request):
        """Get badges earned by current user"""
        user_badges = UserBadge.objects.filter(user=request.user).select_related(
            "badge"
        )
        serializer = UserBadgeSerializer(user_badges, many=True)
        return Response(serializer.data)


class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing available levels"""

    queryset = Level.objects.all().order_by("level_number")
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated]


class ProgressUpdateAPIView(APIView):
    """API endpoint for other apps to update user progress"""

    permission_classes = []  # Open endpoint for internal app communication

    def post(self, request):
        """Update user progress and award points/achievements"""
        serializer = ProgressUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = ProgressService.update_user_progress(**serializer.validated_data)

        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class LeaderboardAPIView(APIView):
    """API endpoint for getting leaderboard"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get top users leaderboard"""
        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
            limit = min(limit, 50)  # Cap at 50
        except ValueError:
            limit = 10

        top_users = ProgressService.get_leaderboard(limit)
        serializer = UserStatsSerializer(top_users, many=True)
        return Response(serializer.data)


class UserStatsAPIView(APIView):
    """API endpoint for getting detailed user statistics"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        """Get user stats - current user if no user_id provided"""
        if user_id is None:
            user_id = request.user.id

        stats = ProgressService.get_user_stats(user_id)
        if not stats:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the data
        profile_data = UserProfileSerializer(stats["profile"]).data
        badges_data = UserBadgeSerializer(stats["badges"], many=True).data
        transactions_data = PointsTransactionSerializer(
            stats["recent_transactions"], many=True
        ).data

        next_badge_data = None
        if stats["next_badge"]:
            next_badge_data = BadgeSerializer(stats["next_badge"]).data

        next_level_data = None
        if stats["next_level"]:
            next_level_data = LevelSerializer(stats["next_level"]).data

        return Response(
            {
                "profile": profile_data,
                "badges": badges_data,
                "recent_transactions": transactions_data,
                "next_badge": next_badge_data,
                "next_level": next_level_data,
            }
        )


class PointsHistoryAPIView(APIView):
    """API endpoint for getting user's points transaction history"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's points transaction history"""
        transactions = PointsTransaction.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        # Pagination
        page_size = 20
        page = request.query_params.get("page", 1)
        try:
            page = int(page)
            start = (page - 1) * page_size
            end = start + page_size
            transactions = transactions[start:end]
        except ValueError:
            pass

        serializer = PointsTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
