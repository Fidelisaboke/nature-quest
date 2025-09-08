from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class Challenge(models.Model):
    """Predefined challenges for users to complete"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    LOCATION_TYPES = [
        ('park', 'Park'),
        ('forest', 'Forest'),
        ('lake', 'Lake'),
        ('mountain', 'Mountain'),
        ('beach', 'Beach'),
        ('garden', 'Garden'),
        ('trail', 'Trail'),
        ('wildlife_area', 'Wildlife Area'),
        ('nature_reserve', 'Nature Reserve'),
        ('river', 'River'),
        ('waterfall', 'Waterfall'),
        ('desert', 'Desert'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    location_name = models.CharField(max_length=200, help_text="Name of the specific location")
    
    # Geographic coordinates for verification
    target_latitude = models.FloatField(help_text="Target latitude for location verification")
    target_longitude = models.FloatField(help_text="Target longitude for location verification")
    verification_radius = models.IntegerField(default=500, help_text="Verification radius in meters")
    
    # Challenge requirements
    required_elements = models.JSONField(default=list, help_text="Elements that should be in the photo")
    special_instructions = models.TextField(blank=True, help_text="Special instructions for the challenge")
    points_reward = models.IntegerField(validators=[MinValueValidator(0)])
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['difficulty_level', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.difficulty_level})"


class ChallengeAttempt(models.Model):
    """User attempts at completing challenges"""
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('failed', 'Failed Verification'),
        ('flagged', 'Flagged for Review'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_attempts')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='attempts')
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Submitted data
    submitted_photo = models.ImageField(upload_to='challenge_submissions/%Y/%m/%d/')
    submitted_latitude = models.FloatField()
    submitted_longitude = models.FloatField()
    submitted_description = models.TextField(blank=True)
    
    # Verification results
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.verification_status})"
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'


class PhotoAnalysis(models.Model):
    """Analysis results for submitted photos"""
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='photo_analysis')
    
    # Analysis scores
    quality_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    authenticity_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Detection results
    detected_objects = models.JSONField(default=list, help_text="Objects detected in the photo")
    exif_data = models.JSONField(default=dict, help_text="EXIF metadata from the photo")
    
    # Verification results
    verification_passed = models.BooleanField(default=False)
    analysis_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Photo Analysis - {self.attempt}"


class LocationVerification(models.Model):
    """Location verification results"""
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='location_verification')
    
    # Distance verification
    is_within_radius = models.BooleanField(default=False)
    distance_to_target = models.FloatField(help_text="Distance in meters to target location")
    
    # External API verification
    foursquare_data = models.JSONField(default=dict, help_text="Data from Foursquare API")
    verification_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for location verification"
    )
    
    # Overall verification result
    verification_passed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Location Verification - {self.attempt}"


class VerificationMetrics(models.Model):
    """Performance metrics for verification processes"""
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='verification_metrics')
    
    # Processing times (in seconds)
    photo_analysis_time = models.FloatField(default=0.0)
    location_verification_time = models.FloatField(default=0.0)
    fraud_detection_time = models.FloatField(default=0.0)
    total_processing_time = models.FloatField(default=0.0)
    
    # API usage tracking
    api_calls_made = models.JSONField(default=list, help_text="List of API calls made during verification")
    processing_errors = models.JSONField(default=list, help_text="Any errors encountered during processing")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification Metrics - {self.attempt}"


class FraudDetection(models.Model):
    """Fraud detection and risk assessment for submissions"""
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='fraud_detection')
    
    # Risk assessment
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    risk_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    risk_factors = models.JSONField(default=list, help_text="List of identified risk factors")
    
    # Manual review
    requires_manual_review = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    manual_review_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Fraud Detection - {self.attempt} ({self.risk_level})"
    
    @property
    def completion_count(self):
        """Get number of times this challenge has been completed"""
        return ChallengeAttempt.objects.filter(challenge=self, status='verified').count()


class ChallengeAttempt(models.Model):
    """User's attempt to complete a challenge"""
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('failed', 'Verification Failed'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_attempts')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Submitted data
    submitted_photo = models.ImageField(upload_to='challenge_submissions/')
    submitted_latitude = models.FloatField()
    submitted_longitude = models.FloatField()
    submission_notes = models.TextField(blank=True)
    
    # Verification results
    photo_verified = models.BooleanField(default=False)
    location_verified = models.BooleanField(default=False)
    verification_details = models.JSONField(default=dict)
    
    # Points and rewards
    points_earned = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'challenge')  # One attempt per challenge per user
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.status})"
    
    @property
    def is_verified(self):
        return self.status == 'verified'
    
    @property
    def total_points(self):
        return self.points_earned + self.bonus_points


class PhotoAnalysis(models.Model):
    """Analysis results for submitted photos"""
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='photo_analysis')
    
    # EXIF data
    exif_data = models.JSONField(default=dict)
    has_location_data = models.BooleanField(default=False)
    photo_latitude = models.FloatField(null=True, blank=True)
    photo_longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    camera_info = models.JSONField(default=dict)
    
    # Image analysis
    detected_objects = models.JSONField(default=list)
    confidence_scores = models.JSONField(default=dict)
    image_quality_score = models.FloatField(default=0.0)
    authenticity_score = models.FloatField(default=0.0)
    
    # Nature elements detection
    nature_elements = models.JSONField(default=list)
    element_confidence = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analysis for {self.attempt}"


class LocationVerification(models.Model):
    """Location verification results using external APIs"""
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='location_verification')
    
    # Foursquare verification
    foursquare_places = models.JSONField(default=list)
    closest_match = models.JSONField(default=dict)
    distance_to_match = models.FloatField(null=True, blank=True)
    location_type_match = models.BooleanField(default=False)
    
    # Geographic validation
    is_valid_coordinate = models.BooleanField(default=True)
    country_code = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=100, blank=True)
    
    # Additional context
    nearby_landmarks = models.JSONField(default=list)
    verification_confidence = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Location verification for {self.attempt}"


class VerificationMetrics(models.Model):
    """Analytics for challenge verification performance"""
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, related_name='metrics')
    
    total_attempts = models.IntegerField(default=0)
    successful_verifications = models.IntegerField(default=0)
    failed_verifications = models.IntegerField(default=0)
    average_verification_time = models.FloatField(default=0.0)  # seconds
    
    # Common failure reasons
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
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    attempt = models.OneToOneField(ChallengeAttempt, on_delete=models.CASCADE, related_name='fraud_detection')
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='low')
    
    # Risk factors
    duplicate_image_detected = models.BooleanField(default=False)
    suspicious_location = models.BooleanField(default=False)
    metadata_inconsistencies = models.BooleanField(default=False)
    rapid_submissions = models.BooleanField(default=False)
    
    # Analysis details
    risk_factors = models.JSONField(default=list)
    confidence_score = models.FloatField(default=0.0)
    requires_manual_review = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_reviews')
    
    def __str__(self):
        return f"Fraud check: {self.attempt} - {self.risk_level}"
