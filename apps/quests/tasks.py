from datetime import timezone
import logging
from celery import shared_task
from .models import QuestLog, ChallengeLog, TriviaQuestion

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def update_quest_progress(self, quest_log_id):
    try:
        in_progress_quests = QuestLog.objects.filter(
            user=self.request.user,
            status='in_progress'
        ).select_related('quest', 'quest__challenges', 'quest__trivia_questions').all()
        
        updated_count = 0
        now = timezone.now()

        for progress in in_progress_quests:
            # Check if quest has expired
            if progress.quest.expiry_date and progress.quest.expiry_date < now:
                progress.status = 'abandoned'
                progress.save()
                updated_count += 1
                continue

            # Check if all challenges are completed
            total_challenges = progress.quest.challenges.count()
            completed_challenges = progress.quest.challenges.filter(challenge_logs__user=progress.user, challenge_logs__status='completed').count()
            
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
                        progress.user.experience += progress.quest.experience_reward
                        progress.user.save(update_fields=['experience_points'])
                        
                        