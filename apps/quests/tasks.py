from datetime import timezone
import logging
from celery import shared_task
from .models import QuestLog

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def update_quest_progress(self, quest_log_id):
    try:
        quest_log = QuestLog.objects.get(id=quest_log_id)
        user = quest_log.user
        in_progress_quests = QuestLog.objects.filter(
            user=user,
            status='in_progress'
        ).select_related('quest', 'quest__challenges', 'quest__trivia_questions').all()
        
        updated_count = 0
        now = timezone.now()

        for progress in in_progress_quests:
            # Check if all challenges are completed
            total_challenges = progress.quest.challenges.count()
            completed_challenges = progress.quest.challenges.filter(challenge_logs__user=progress.user).count()
            
            # Update progress percentage
            if total_challenges > 0:
                new_progress = int((completed_challenges / total_challenges) * 100)
                if new_progress != progress.progress:
                    progress.progress = new_progress

                    # Mark quest as completed if progress is 100%
                    if new_progress == 100:
                        progress.status = 'completed'
                        progress.end_time = now

                        # Award experience points to user
                        progress.user.profile.points += progress.quest.experience_reward
                        progress.experience_earned = progress.quest.experience_reward
                        progress.user.profile.save(update_fields=['points'])
                    
                    progress.save(
                        update_fields=['progress', 'status', 'end_time', 'experience_earned']
                    )
                    updated_count += 1
        
        logger.info(f"Updated {updated_count} quest progress records")
        return f"Updated {updated_count} quest progress records"
    
    except Exception as e:
        logger.error(f"Failed to update quest progress: {e}", exc_info=True)
        self.retry(exc=e, countdown=60 * 5)
        return f"Failed to update quest progress: {e}"