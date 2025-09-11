from django.db import transaction
import logging
from celery import shared_task
from .models import QuestLog
from django.db.models import F
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