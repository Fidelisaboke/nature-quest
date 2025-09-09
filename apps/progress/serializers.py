from rest_framework import serializers
from .models import UserProfile, Badge, Level, UserBadge, PointsTransaction


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["level_number", "name", "points_required", "description"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "animal",
            "name",
            "description",
            "points_required",
            "is_special",
            "icon_url",
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ["badge", "earned_at", "points_when_earned"]


class PointsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTransaction
        fields = [
            "transaction_type",
            "points",
            "description",
            "challenge_id",
            "quiz_id",
            "created_at",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    earned_badges = UserBadgeSerializer(many=True, read_only=True)
    current_level = LevelSerializer(read_only=True)
    quiz_difficulty_level = serializers.ReadOnlyField()
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    tech_stacks_list = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "is_techie",
            "tech_stacks",
            "tech_stacks_list",
            "total_points",
            "current_level",
            "challenges_completed",
            "quizzes_completed",
            "quiz_difficulty_level",
            "earned_badges",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["total_points", "challenges_completed", "quizzes_completed"]

    def get_tech_stacks_list(self, obj):
        """Convert comma-separated tech stacks to list"""
        if obj.tech_stacks:
            return [
                stack.strip() for stack in obj.tech_stacks.split(",") if stack.strip()
            ]
        return []

    def update(self, instance, validated_data):
        """Allow updating tech preferences"""
        instance.is_techie = validated_data.get("is_techie", instance.is_techie)
        instance.tech_stacks = validated_data.get("tech_stacks", instance.tech_stacks)
        instance.save()
        return instance


class UserStatsSerializer(serializers.ModelSerializer):
    """Simplified serializer for leaderboard and stats"""

    username = serializers.CharField(source="user.username", read_only=True)
    badges_count = serializers.SerializerMethodField()
    current_level_name = serializers.CharField(
        source="current_level.name", read_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "total_points",
            "current_level_name",
            "badges_count",
            "challenges_completed",
            "quizzes_completed",
        ]

    def get_badges_count(self, obj):
        return obj.user.badges.count()


class ProgressUpdateSerializer(serializers.Serializer):
    """Serializer for updating user progress from external apps"""

    user_id = serializers.IntegerField()
    points_to_add = serializers.IntegerField(min_value=0)
    transaction_type = serializers.ChoiceField(
        choices=PointsTransaction.TRANSACTION_TYPES
    )
    description = serializers.CharField(max_length=200)
    challenge_id = serializers.IntegerField(required=False, allow_null=True)
    quiz_id = serializers.IntegerField(required=False, allow_null=True)
    increment_challenges = serializers.BooleanField(default=False)
    increment_quizzes = serializers.BooleanField(default=False)
