from calendar import c
from email.policy import default
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from users.models import RegisterUser

# Create your models here.
class Quest(models.Model):
    QUEST_TYPES = [
        ('outdoor', 'Outdoor Adventure'),
        ('indoor', 'Indoor Challenge'),
        ('team', 'Team Quest'),
        ('individual', 'Individual Quest'),
    ]

    DIFFICULTY_LEVELS = [
        (1, 'Easy'),
        (2, 'Moderate'),
        (3, 'Challenging'),
        (4, 'Difficult'),
        (5, 'Expert'),
        (6, 'Rare'),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    quest_type = models.CharField(max_length=20, choices=QUEST_TYPES)
    difficulty = models.PositiveSmallIntegerField(
        choices=DIFFICULTY_LEVELS,
        default=1,
        validators = [MinValueValidator(1), MaxValueValidator(6)]
    )
    duration_minutes = models.DurationField(help_text="Estimated duration in minutes")
    experience_reward = models.PositiveIntegerField(help_text="Experience points reward")
    requirements = models.JSONField(default=dict)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_quest_type_display()} - {self.title}"

    def get_quest_type_display(self):
        return dict(self.QUEST_TYPES)[self.quest_type]

    def get_difficulty_display(self):
        return dict(self.DIFFICULTY_LEVELS)[self.difficulty]

    def get_duration_minutes_display(self):
        return self.duration_minutes.total_seconds() / 60

class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    distance = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True, index=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_address_display(self):
        return self.address

    def get_source_display(self):
        return self.source
    
    def get_metadata_display(self):
        return self.metadata

    class Meta:
        verbose_name_plural = "Locations"

class Challenge(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    quests = models.ManyToManyField(Quest, related_name='challenges')
    description = models.TextField()
    is_mandatory = models.BooleanField(default=False)
    experience_reward = models.PositiveIntegerField(help_text="Experience points reward for completing the challenge")
    order = models.PositiveSmallIntegerField(default=1, help_text="Order of the challenge in the list")   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quests.title} - {self.title}"

    def get_quests_display(self):
        return self.quests.title

    class Meta:
        verbose_name_plural = "Challenges"
        ordering = ['order']

class QuestLog(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
        ('not_started', 'Not Started'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(RegisterUser, on_delete=models.CASCADE, related_name="quest_logs")
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name="quest_logs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    progress = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    experience_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.quest.title}"

    class Meta:
        verbose_name_plural = "Quest Logs"
        ordering = ['start_time']
        unique_together = ('user', 'quest')

class ChallengeLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(RegisterUser, on_delete=models.CASCADE, related_name="challenge_logs")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="challenge_logs")
    completed_at = models.DateTimeField(auto_now_add=True)
    experience_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"

    class Meta:
        verbose_name_plural = "Challenge Logs"
        ordering = ['completed_at']
        unique_together = ('user', 'challenge')

class TriviaQuestion(models.Model):
    id = models.AutoField(primary_key=True)
    question_text = models.CharField(max_length=255)
    choices = models.JSONField(default=list)
    correct_answer = models.CharField(max_length=255)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.question_text
    
    class Meta:
        verbose_name_plural = "Trivia Questions"
        ordering = ['question_text']
    