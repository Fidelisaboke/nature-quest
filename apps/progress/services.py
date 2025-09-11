from django.contrib.auth import get_user_model
from django.db import transaction
from .models import UserProfile, Badge, Level, UserBadge, PointsTransaction
import logging

logger = logging.getLogger(__name__)


User = get_user_model()

class ProgressService:
    """Service for managing user progress, points, badges, and level ups"""

    @staticmethod
    def update_user_progress(
        user_id,
        points_to_add,
        transaction_type,
        description,
        challenge_id=None,
        quiz_id=None,
        increment_challenges=False,
        increment_quizzes=False,
    ):
        """
        Update user progress with points and check for badge/level eligibility
        Returns: dict with success status and any achievements unlocked
        """
        try:
            with transaction.atomic():
                user = User.objects.get(id=user_id)
                profile, created = UserProfile.objects.get_or_create(user=user)

                # Add points
                old_points = profile.total_points
                profile.total_points += points_to_add

                # Increment counters if requested
                if increment_challenges:
                    profile.challenges_completed += 1
                if increment_quizzes:
                    profile.quizzes_completed += 1

                profile.save()

                # Create points transaction record
                PointsTransaction.objects.create(
                    user=user,
                    transaction_type=transaction_type,
                    points=points_to_add,
                    description=description,
                    challenge_id=challenge_id,
                    quiz_id=quiz_id,
                )

                # Check for new achievements
                achievements = ProgressService._check_achievements(
                    user, profile, old_points
                )

                logger.info(
                    f"Updated progress for user {user.username}: +{points_to_add} points"
                )

                return {
                    "success": True,
                    "new_total_points": profile.total_points,
                    "achievements": achievements,
                }

        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            return {"success": False, "error": "User not found"}
        except Exception as e:
            logger.error(f"Error updating progress for user {user_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _check_achievements(user, profile, old_points):
        """Check and award new badges and levels"""
        achievements = {"new_badges": [], "new_level": None, "bonus_points": 0}

        # Check for new badges (consecutive 250 point increments)
        current_points = profile.total_points

        # Calculate badge eligibility based on consecutive 250 point increments
        badges_available = (
            Badge.objects.filter(points_required__lte=current_points)
            .exclude(id__in=user.badges.values_list("badge_id", flat=True))
            .order_by("points_required")
        )

        for badge in badges_available:
            # Skip special Cat badge unless special conditions are met
            if (
                badge.is_special
                and not ProgressService._check_special_badge_eligibility(user, profile)
            ):
                continue

            UserBadge.objects.create(
                user=user, badge=badge, points_when_earned=current_points
            )
            achievements["new_badges"].append(
                {
                    "name": badge.name,
                    "animal": badge.animal,
                    "description": badge.description,
                }
            )

            # Award bonus points for earning badge
            bonus_points = 50
            profile.total_points += bonus_points
            achievements["bonus_points"] += bonus_points

            PointsTransaction.objects.create(
                user=user,
                transaction_type="badge_earned",
                points=bonus_points,
                description=f"Bonus for earning {badge.name} badge",
            )

        # Check for level up
        old_level = profile.current_level
        new_level = (
            Level.objects.filter(points_required__lte=profile.total_points)
            .order_by("-level_number")
            .first()
        )

        if new_level and (
            not old_level or new_level.level_number > old_level.level_number
        ):
            profile.current_level = new_level

            # Award level up bonus
            level_bonus = new_level.level_number * 100
            profile.total_points += level_bonus
            achievements["bonus_points"] += level_bonus

            PointsTransaction.objects.create(
                user=user,
                transaction_type="level_up",
                points=level_bonus,
                description=f"Level up bonus to {new_level.name}",
            )

            achievements["new_level"] = {
                "level_number": new_level.level_number,
                "name": new_level.name,
                "description": new_level.description,
                "bonus_points": level_bonus,
            }

        profile.save()
        return achievements

    @staticmethod
    def _check_special_badge_eligibility(user, profile):
        """Check if user is eligible for special Cat badge"""
        # Special conditions for Cat badge:
        # - Must have earned all 12 regular animal badges
        # - Must be at level 10 or higher
        # - Must have completed at least 20 challenges
        regular_badges_count = user.badges.filter(badge__is_special=False).count()
        return (
            regular_badges_count >= 12
            and profile.current_level
            and profile.current_level.level_number >= 10
            and profile.challenges_completed >= 20
        )

    @staticmethod
    def get_user_stats(user_id):
        """Get comprehensive user statistics"""
        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfile.objects.get_or_create(user=user)

            badges = user.badges.select_related("badge").order_by("-earned_at")
            recent_transactions = user.points_transactions.order_by("-created_at")[:10]

            return {
                "profile": profile,
                "badges": badges,
                "recent_transactions": recent_transactions,
                "next_badge": ProgressService._get_next_badge(profile),
                "next_level": ProgressService._get_next_level(profile),
            }
        except User.DoesNotExist:
            return None

    @staticmethod
    def _get_next_badge(profile):
        """Get the next badge user can earn"""
        earned_badge_ids = profile.user.badges.values_list("badge_id", flat=True)
        next_badge = (
            Badge.objects.filter(points_required__gt=profile.total_points)
            .exclude(id__in=earned_badge_ids)
            .exclude(
                is_special=True  # Don't show special badge in regular progression
            )
            .order_by("points_required")
            .first()
        )

        return next_badge

    @staticmethod
    def _get_next_level(profile):
        """Get the next level user can reach"""
        if profile.current_level:
            return (
                Level.objects.filter(
                    level_number__gt=profile.current_level.level_number
                )
                .order_by("level_number")
                .first()
            )
        else:
            return Level.objects.order_by("level_number").first()

    @staticmethod
    def get_leaderboard(limit=10):
        """Get top users by points"""
        return UserProfile.objects.select_related("user", "current_level").order_by(
            "-total_points"
        )[:limit]
