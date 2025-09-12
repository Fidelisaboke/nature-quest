from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from apps.users.models import RegisterUser

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
    # Spatial point field for better geospatial operations
    point = gis_models.PointField(
        geography=True,  # Uses geodetic calculations (WGS84)
        srid=4326,       # Standard WGS84 SRID
        null=True,       # Allow null for flexibility
        blank=True,
        help_text='Longitude, Latitude coordinates'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-90, 'Latitude must be at least -90 degrees.'),
            MaxValueValidator(90, 'Latitude must be at most 90 degrees.')
        ],
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-180, 'Longitude must be at least -180 degrees.'),
            MaxValueValidator(180, 'Longitude must be at most 180 degrees.')
        ],
        null=True,
        blank=True
    )
    address = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    distance = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        validators=[
            MinValueValidator(0, 'Distance cannot be negative.')
        ],
        blank=True,
        null=True
    )
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
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(
                        latitude__isnull=False,
                        longitude__isnull=False,
                        latitude__gte=-90,
                        latitude__lte=90,
                        longitude__gte=-180,
                        longitude__lte=180,
                        distance__isnull=False,
                        distance__gte=0
                    ) | models.Q(
                        latitude__isnull=True,
                        longitude__isnull=True,
                        distance__isnull=True
                    )
                ),
                name='valid_geo_coordinates_and_distance'
            )
        ]
    
    def clean(self):
        super().clean()
        # Ensure point field is in sync with lat/lng
        if self.latitude is not None and self.longitude is not None:
            if not (-90 <= float(self.latitude) <= 90):
                raise ValidationError({'latitude': 'Latitude must be between -90 and 90 degrees.'})
            if not (-180 <= float(self.longitude) <= 180):
                raise ValidationError({'longitude': 'Longitude must be between -180 and 180 degrees.'})
            self.point = Point(float(self.longitude), float(self.latitude), srid=4326)
        elif self.point:
            self.longitude = self.point.x
            self.latitude = self.point.y
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def coordinates(self):
        """Return coordinates as a (longitude, latitude) tuple if available."""
        if self.point:
            return (self.point.x, self.point.y)
        elif self.longitude is not None and self.latitude is not None:
            return (float(self.longitude), float(self.latitude))
        return None

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
        return self.title

    def get_quests_display(self, limit: int = 3) -> str:
        # Use prefetched quests if available, otherwise fall back to querying
        quests = getattr(self, '_prefetched_objects_cache', {}).get('quests', None)
        if quests is None:
            quests = list(self.quests.all()[:limit + 1])
        else:
            quests = list(quests[:limit + 1])
            
        titles = [q.title for q in quests]
        more = f" +{len(titles) - limit} more" if len(titles) > limit else ""
        return ", ".join(titles[:limit]) + more
    
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
    choices = models.JSONField(
        default=list,
        help_text="List of available answer choices"
    )
    correct_answer = models.CharField(
        max_length=255,
        help_text="Must be one of the values from the choices list"
    )
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        super().clean()
        if self.choices and self.correct_answer:
            if self.correct_answer not in self.choices:
                raise ValidationError({
                    'correct_answer': f'"{self.correct_answer}" must be one of the choices: {self.choices}'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.question_text
    
    class Meta:
        verbose_name_plural = "Trivia Questions"
        ordering = ['question_text']
        
