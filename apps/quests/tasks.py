from django.db import transaction
import logging
from celery import shared_task
from .models import QuestLog, Quest, UserProgressCheckpoint, Badge, UserBadge, CarbonImpact, LeaderboardEntry
from apps.users.models import RegisterUser
from django.db.models import F, Sum, Count
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def update_quest_progress(self, quest_log_id):
    try:
        quest_log = QuestLog.objects.get(id=quest_log_id)
        user = quest_log.user
        in_progress_quests = (
            QuestLog.objects
            .filter(user=user, status='in_progress')
            .select_related('quest', 'user__profile')
            .prefetch_related('quest__challenges', 'quest__trivia_questions')
        )
        updated_count = 0
        now = timezone.now()

        for progress in in_progress_quests:
            with transaction.atomic():
                try:
                    # Lock the QuestLog row for update
                    locked_progress = QuestLog.objects.select_for_update().get(pk=progress.pk)
                    
                    # Re-fetch the latest state after acquiring the lock
                    completed_challenges = locked_progress.challenge_logs.filter(completed=True).count()
                    total_challenges = locked_progress.quest.challenges.count()
                    
                    if total_challenges > 0:
                        new_progress = min(100, int((completed_challenges / total_challenges) * 100))
                        
                        # Only proceed if there are actual changes to save
                        if new_progress != locked_progress.progress or (new_progress == 100 and locked_progress.status != 'completed'):
                            # Update quest progress
                            locked_progress.progress = new_progress
                            
                            # Mark as completed if progress is 100%
                            if new_progress == 100 and locked_progress.status != 'completed':
                                locked_progress.status = 'completed'
                                locked_progress.end_time = now
                                locked_progress.experience_earned = locked_progress.quest.experience_reward
                                
                                # Atomically update user points
                                locked_progress.user.profile.__class__.objects.filter(
                                    pk=locked_progress.user.profile.pk
                                ).update(points=F('points') + locked_progress.quest.experience_reward)
                            
                            # Save the progress with updated fields
                            update_fields = ['progress', 'updated_at']
                            if locked_progress.status == 'completed':
                                update_fields.extend(['status', 'end_time', 'experience_earned'])
                                
                            locked_progress.save(update_fields=update_fields)
                            updated_count += 1
                            
                except QuestLog.DoesNotExist:
                    logger.warning(f"QuestLog {progress.pk} not found, skipping update")
                    continue
        
        logger.info(f"Updated {updated_count} quest progress records")
        return f"Updated {updated_count} quest progress records"
    
    except Exception as e:
        logger.error(f"Failed to update quest progress: {e}", exc_info=True)
        self.retry(exc=e, countdown=60 * 5)
        return f"Failed to update quest progress: {e}"


@shared_task(bind=True, max_retries=3)
def process_quest_completion(self, quest_log_id):
    """
    Comprehensive quest completion processing:
    - Award XP and update level
    - Check and award badges
    - Calculate carbon impact
    - Update leaderboards
    """
    try:
        quest_log = QuestLog.objects.select_related(
            'user', 'user__profile', 'quest'
        ).get(id=quest_log_id)

        user = quest_log.user
        profile = user.profile
        quest = quest_log.quest

        with transaction.atomic():
            # 1. Award XP and check level up
            xp_gained = quest.experience_reward
            profile.points += xp_gained

            # Check for level up
            new_level = calculate_level_from_xp(profile.points)
            level_up = new_level > profile.level
            profile.level = new_level
            profile.save()

            # 2. Calculate carbon impact
            carbon_impact = calculate_carbon_impact(quest_log)

            # 3. Check for new badges
            new_badges = check_and_award_badges(user)

            # 4. Update leaderboards
            update_leaderboard_entries.delay(user.id)

            # 5. Check challenge completion
            check_challenge_completion.delay(user.id, quest.id)

        return {
            'quest_log_id': quest_log_id,
            'xp_gained': xp_gained,
            'level_up': level_up,
            'new_level': new_level if level_up else None,
            'carbon_saved': carbon_impact.carbon_saved_kg if carbon_impact else 0,
            'new_badges': [b.badge.name for b in new_badges]
        }

    except Exception as e:
        logger.error(f"Quest completion processing failed: {e}", exc_info=True)
        self.retry(exc=e, countdown=60 * 5)


def calculate_level_from_xp(total_xp):
    """Calculate user level from total XP using exponential curve."""
    import math
    # Level = (XP / 100) ^ (2/3)
    level = int(math.pow(total_xp / 100, 2/3))
    return max(1, level)


@shared_task
def calculate_carbon_impact(quest_log):
    """
    Calculate environmental impact based on quest activity.
    Uses activity-based estimates with GPS distance when available.
    """
    quest = quest_log.quest

    # Base carbon savings per quest type (kg CO2 vs car travel)
    CARBON_RATES = {
        'outdoor': 0.12,      # per km walked
        'indoor': 0.08,       # minimal savings
        'team': 0.10,         # shared transportation avoided
        'individual': 0.12,   # personal car avoided
    }

    # Estimate distance from quest duration (avg walking speed 5km/h)
    hours = quest.duration_minutes.total_seconds() / 3600
    estimated_distance = hours * 5  # km

    # Check for actual GPS-tracked distance from checkpoints
    actual_distance = UserProgressCheckpoint.objects.filter(
        quest_log=quest_log
    ).count() * 0.5  # Estimate 0.5km per checkpoint visited

    distance_km = actual_distance or estimated_distance
    carbon_saved = distance_km * CARBON_RATES.get(quest.quest_type, 0.10)

    # Trees equivalent (avg tree absorbs ~22kg CO2/year)
    trees_equivalent = carbon_saved / 22

    impact, created = CarbonImpact.objects.get_or_create(
        quest_log=quest_log,
        defaults={
            'user': quest_log.user,
            'activity_type': quest.quest_type,
            'distance_km': distance_km,
            'carbon_saved_kg': carbon_saved,
            'trees_equivalent': trees_equivalent
        }
    )

    return impact


@shared_task
def check_and_award_badges(user):
    """
    Check all badge requirements and award new badges.
    """
    new_badges = []
    user_badges = {
        ub.badge_id: ub for ub in UserBadge.objects.filter(user=user)
    }

    all_badges = Badge.objects.all()

    for badge in all_badges:
        user_badge = user_badges.get(badge.id)

        # Skip if already complete
        if user_badge and user_badge.is_complete:
            continue

        # Calculate progress based on requirement type
        progress = calculate_badge_progress(user, badge)

        if not user_badge:
            user_badge = UserBadge.objects.create(
                user=user,
                badge=badge,
                progress=progress,
                is_complete=progress >= badge.requirement_value
            )
        else:
            user_badge.progress = progress
            user_badge.is_complete = progress >= badge.requirement_value
            if user_badge.is_complete:
                user_badge.save()

        if user_badge.is_complete:
            new_badges.append(user_badge)

    return new_badges


def calculate_badge_progress(user, badge):
    """Calculate user's current progress toward a badge."""
    if badge.requirement_type == 'quest_count':
        queryset = QuestLog.objects.filter(user=user, status='completed')
        if badge.quest_type_filter:
            queryset = queryset.filter(quest__quest_type=badge.quest_type_filter)
        return queryset.count()

    elif badge.requirement_type == 'xp_threshold':
        return user.profile.points

    elif badge.requirement_type == 'streak_days':
        # Calculate consecutive days with quest completions
        return calculate_streak_days(user)

    elif badge.requirement_type == 'carbon_saved':
        total = CarbonImpact.objects.filter(user=user).aggregate(
            total=Sum('carbon_saved_kg')
        )['total'] or 0
        return int(total * 1000)  # Convert to grams for integer storage

    elif badge.requirement_type == 'category_diversity':
        # Number of different quest types completed
        return QuestLog.objects.filter(
            user=user,
            status='completed'
        ).values('quest__quest_type').distinct().count()

    return 0


def calculate_streak_days(user):
    """Calculate consecutive days with quest completions."""
    from datetime import timedelta

    completions = QuestLog.objects.filter(
        user=user,
        status='completed'
    ).values_list('end_time__date', flat=True).distinct().order_by('-end_time__date')

    if not completions:
        return 0

    streak = 0
    today = timezone.now().date()
    expected_date = today

    for completion_date in completions:
        if completion_date == expected_date or completion_date == today:
            streak += 1
            expected_date -= timedelta(days=1)
        elif completion_date < expected_date:
            break

    return streak


@shared_task
def update_leaderboard_entries(user_id):
    """Update all leaderboard entries for a user."""
    user = RegisterUser.objects.get(id=user_id)
    profile = user.profile

    # Global XP leaderboard
    update_leaderboard_entry(user, 'global_xp', '', None, profile.points)

    # Regional XP leaderboard (based on user's region)
    if profile.region:
        update_leaderboard_entry(user, 'regional_xp', profile.region, None, profile.points)

    # Category-specific leaderboards
    for quest_type, _ in Quest.QUEST_TYPES:
        category_xp = QuestLog.objects.filter(
            user=user,
            status='completed',
            quest__quest_type=quest_type
        ).aggregate(total=Sum('quest__experience_reward'))['total'] or 0

        update_leaderboard_entry(user, 'category_xp', '', quest_type, category_xp)

    # Environmental impact leaderboard
    environmental_score = CarbonImpact.objects.filter(user=user).aggregate(
        total=Sum('carbon_saved_kg')
    )['total'] or 0
    update_leaderboard_entry(user, 'environmental', '', None, int(environmental_score * 1000))


def update_leaderboard_entry(user, lb_type, region, quest_type, score):
    """Update or create a leaderboard entry."""
    entry, created = LeaderboardEntry.objects.update_or_create(
        user=user,
        leaderboard_type=lb_type,
        region=region,
        quest_type=quest_type,
        period='all_time',
        defaults={'score': score}
    )

    # Recalculate ranks (this could be optimized to run less frequently)
    recalculate_ranks.delay(lb_type, region, quest_type, 'all_time')


@shared_task
def recalculate_ranks(leaderboard_type, region, quest_type, period):
    """Recalculate rankings for a specific leaderboard."""
    entries = LeaderboardEntry.objects.filter(
        leaderboard_type=leaderboard_type,
        region=region,
        quest_type=quest_type,
        period=period
    ).order_by('-score')

    for rank, entry in enumerate(entries, 1):
        entry.rank = rank
        entry.save(update_fields=['rank'])


@shared_task
def check_challenge_completion(user_id, quest_id):
    """Check if completing a quest completes any challenges."""
    from .models import Challenge, ChallengeLog

    user = RegisterUser.objects.get(id=user_id)
    quest = Quest.objects.get(id=quest_id)

    # Find challenges containing this quest
    challenges = Challenge.objects.filter(quests=quest)

    for challenge in challenges:
        # Check if all quests in challenge are completed
        total_quests = challenge.quests.count()
        completed_quests = QuestLog.objects.filter(
            user=user,
            quest__in=challenge.quests.all(),
            status='completed'
        ).count()

        if completed_quests >= total_quests:
            # Award challenge completion
            ChallengeLog.objects.get_or_create(
                user=user,
                challenge=challenge,
                defaults={'experience_earned': challenge.experience_reward}
            )

            # Update user XP
            user.profile.points += challenge.experience_reward
            user.profile.save()