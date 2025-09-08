from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Level(models.Model):
    """12 Gemstone/Mineral levels ordered by rarity and value"""
    LEVEL_CHOICES = [
        (1, 'Quartz'),
        (2, 'Amethyst'),
        (3, 'Citrine'),
        (4, 'Turquoise'),
        (5, 'Garnet'),
        (6, 'Peridot'),
        (7, 'Topaz'),
        (8, 'Sapphire'),
        (9, 'Ruby'),
        (10, 'Emerald'),
        (11, 'Diamond'),
        (12, 'Tanzanite'),
    ]
    
    level_number = models.IntegerField(unique=True, choices=LEVEL_CHOICES)
    name = models.CharField(max_length=50)
    points_required = models.IntegerField(validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['level_number']
    
    def __str__(self):
        return f"Level {self.level_number}: {self.name}"


class Badge(models.Model):
    """13 Animal badges: 12 Chinese zodiac + Cat (special)"""
    ANIMAL_CHOICES = [
        ('rat', 'Rat'),
        ('ox', 'Ox'),
        ('tiger', 'Tiger'),
        ('rabbit', 'Rabbit'),
        ('dragon', 'Dragon'),
        ('snake', 'Snake'),
        ('horse', 'Horse'),
        ('goat', 'Goat'),
        ('monkey', 'Monkey'),
        ('rooster', 'Rooster'),
        ('dog', 'Dog'),
        ('pig', 'Pig'),
        ('cat', 'Cat'),  # Special final boss badge
    ]
    
    animal = models.CharField(max_length=20, choices=ANIMAL_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.IntegerField(validators=[MinValueValidator(0)])
    is_special = models.BooleanField(default=False)  # For Cat badge
    icon_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} Badge"


class UserProfile(models.Model):
    """Extended user profile with tech preferences and progress tracking"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_techie = models.BooleanField(default=False)
    tech_stacks = models.TextField(blank=True, help_text="Comma-separated list of tech stacks")
    total_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    current_level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    challenges_completed = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    quizzes_completed = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def quiz_difficulty_level(self):
        """Determine quiz difficulty based on challenges completed"""
        if self.challenges_completed <= 8:
            return 'easy'
        elif self.challenges_completed <= 16:
            return 'medium'
        else:
            return 'hard'
    
    @property
    def earned_badges(self):
        """Get all badges earned by this user"""
        return UserBadge.objects.filter(user=self.user).select_related('badge')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserBadge(models.Model):
    """Tracks which badges a user has earned"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    points_when_earned = models.IntegerField(validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class PointsTransaction(models.Model):
    """Track all points earned/spent by users"""
    TRANSACTION_TYPES = [
        ('challenge_completion', 'Challenge Completion'),
        ('quiz_completion', 'Quiz Completion'),
        ('badge_earned', 'Badge Earned'),
        ('level_up', 'Level Up Bonus'),
        ('special_event', 'Special Event'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_transactions')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    points = models.IntegerField()  # Can be negative for spending
    description = models.CharField(max_length=200)
    challenge_id = models.IntegerField(null=True, blank=True)  # Reference to challenge
    quiz_id = models.IntegerField(null=True, blank=True)  # Reference to quiz
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.points} points - {self.description}"
