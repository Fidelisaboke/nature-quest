from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Challenge(models.Model):
    """Predefined challenges for users to complete"""

    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    LOCATION_TYPES = [
        ("park", "Park"),
        ("forest", "Forest"),
        ("lake", "Lake"),
        ("mountain", "Mountain"),
        ("beach", "Beach"),
        ("garden", "Garden"),
        ("trail", "Trail"),
        ("wildlife_area", "Wildlife Area"),
        ("nature_reserve", "Nature Reserve"),
        ("river", "River"),
        ("waterfall", "Waterfall"),
        ("desert", "Desert"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    location_name = models.CharField(
        max_length=200, help_text="Name of the specific location"
    )
    target_latitude = models.FloatField(
        help_text="Target latitude for location verification"
    )
    target_longitude = models.FloatField(
        help_text="Target longitude for location verification"
    )
    verification_radius = models.IntegerField(
        default=500, help_text="Verification radius in meters"
    )
    required_elements = models.JSONField(
        default=list, help_text="Elements that should be in the photo"
    )
    special_instructions = models.TextField(
        blank=True, help_text="Special instructions for the challenge"
    )
    points_reward = models.IntegerField(validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["difficulty_level", "title"]

    def __str__(self):
        return f"{self.title} ({self.difficulty_level})"


class ChallengeAttempt(models.Model):
    """User's attempt to complete a challenge"""

    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("verified", "Verified"),
        ("failed", "Verification Failed"),
        ("rejected", "Rejected"),
        ("flagged", "Flagged for Review"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenge_attempts",
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="attempts"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_photo = models.ImageField(upload_to="challenge_submissions/%Y/%m/%d/")
    submitted_latitude = models.FloatField()
    submitted_longitude = models.FloatField()
    submission_notes = models.TextField(blank=True)
    photo_verified = models.BooleanField(default=False)
    location_verified = models.BooleanField(default=False)
    verification_details = models.JSONField(default=dict)
    points_earned = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "challenge")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.status})"

    @property
    def is_verified(self):
        return self.status == "verified"

    @property
    def total_points(self):
        return self.points_earned + self.bonus_points


class PhotoAnalysis(models.Model):
    """Analysis results for submitted photos"""

    attempt = models.OneToOneField(
        ChallengeAttempt, on_delete=models.CASCADE, related_name="photo_analysis"
    )
    exif_data = models.JSONField(default=dict)
    has_location_data = models.BooleanField(default=False)
    photo_latitude = models.FloatField(null=True, blank=True)
    photo_longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    camera_info = models.JSONField(default=dict)
    detected_objects = models.JSONField(default=list)
    confidence_scores = models.JSONField(default=dict)
    image_quality_score = models.FloatField(default=0.0)
    authenticity_score = models.FloatField(default=0.0)
    nature_elements = models.JSONField(default=list)
    element_confidence = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.attempt}"


class LocationVerification(models.Model):
    """Location verification results using external APIs"""

    attempt = models.OneToOneField(
        ChallengeAttempt, on_delete=models.CASCADE, related_name="location_verification"
    )
    foursquare_places = models.JSONField(default=list)
    closest_match = models.JSONField(default=dict)
    distance_to_match = models.FloatField(null=True, blank=True)
    location_type_match = models.BooleanField(default=False)
    is_valid_coordinate = models.BooleanField(default=True)
    country_code = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=100, blank=True)
    nearby_landmarks = models.JSONField(default=list)
    verification_confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Location verification for {self.attempt}"


class VerificationMetrics(models.Model):
    """Analytics for challenge verification performance"""

    challenge = models.OneToOneField(
        Challenge, on_delete=models.CASCADE, related_name="metrics"
    )
    total_attempts = models.IntegerField(default=0)
    successful_verifications = models.IntegerField(default=0)
    failed_verifications = models.IntegerField(default=0)
    average_verification_time = models.FloatField(default=0.0)
    photo_failures = models.IntegerField(default=0)
    location_failures = models.IntegerField(default=0)
    quality_failures = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Metrics for {self.challenge.title}"

    @property
    def success_rate(self):
        if self.total_attempts > 0:
            return (self.successful_verifications / self.total_attempts) * 100
        return 0.0


class FraudDetection(models.Model):
    """Track potential fraud or suspicious activity"""

    RISK_LEVELS = [
        ("low", "Low Risk"),
        ("medium", "Medium Risk"),
        ("high", "High Risk"),
        ("critical", "Critical Risk"),
    ]
    attempt = models.OneToOneField(
        ChallengeAttempt, on_delete=models.CASCADE, related_name="fraud_detection"
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default="low")
    duplicate_image_detected = models.BooleanField(default=False)
    suspicious_location = models.BooleanField(default=False)
    metadata_inconsistencies = models.BooleanField(default=False)
    rapid_submissions = models.BooleanField(default=False)
    risk_factors = models.JSONField(default=list)
    confidence_score = models.FloatField(default=0.0)
    requires_manual_review = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fraud_reviews",
    )

    def __str__(self):
        return f"Fraud check: {self.attempt} - {self.risk_level}"
