from rest_framework import serializers
from .models import (
    Challenge,
    ChallengeAttempt,
    PhotoAnalysis,
    LocationVerification,
    VerificationMetrics,
    FraudDetection,
)


class ChallengeSerializer(serializers.ModelSerializer):
    completion_count = serializers.ReadOnlyField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "description",
            "difficulty_level",
            "location_type",
            "location_name",
            "target_latitude",
            "target_longitude",
            "required_elements",
            "special_instructions",
            "points_reward",
            "verification_radius",
            "is_active",
            "completion_count",
            "created_at",
        ]


class ChallengeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for challenge lists"""

    completion_count = serializers.ReadOnlyField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "title",
            "difficulty_level",
            "location_type",
            "points_reward",
            "completion_count",
        ]


class PhotoAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoAnalysis
        fields = [
            "exif_data",
            "has_location_data",
            "photo_latitude",
            "photo_longitude",
            "timestamp",
            "detected_objects",
            "confidence_scores",
            "image_quality_score",
            "authenticity_score",
            "nature_elements",
            "element_confidence",
            "created_at",
        ]


class LocationVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationVerification
        fields = [
            "foursquare_places",
            "closest_match",
            "distance_to_match",
            "location_type_match",
            "is_valid_coordinate",
            "country_code",
            "region",
            "nearby_landmarks",
            "verification_confidence",
            "created_at",
        ]


class FraudDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudDetection
        fields = [
            "risk_level",
            "duplicate_image_detected",
            "suspicious_location",
            "metadata_inconsistencies",
            "rapid_submissions",
            "risk_factors",
            "confidence_score",
            "requires_manual_review",
            "created_at",
        ]


class ChallengeAttemptSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    challenge_details = ChallengeListSerializer(source="challenge", read_only=True)
    photo_analysis = PhotoAnalysisSerializer(read_only=True)
    location_verification = LocationVerificationSerializer(read_only=True)
    fraud_detection = FraudDetectionSerializer(read_only=True)
    total_points = serializers.ReadOnlyField()

    class Meta:
        model = ChallengeAttempt
        fields = [
            "id",
            "username",
            "challenge_details",
            "status",
            "submitted_photo",
            "submitted_latitude",
            "submitted_longitude",
            "submission_notes",
            "photo_verified",
            "location_verified",
            "verification_details",
            "points_earned",
            "bonus_points",
            "total_points",
            "created_at",
            "verified_at",
            "photo_analysis",
            "location_verification",
            "fraud_detection",
        ]
        read_only_fields = [
            "status",
            "photo_verified",
            "location_verified",
            "verification_details",
            "points_earned",
            "bonus_points",
            "verified_at",
        ]


class ChallengeSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting a challenge attempt"""

    challenge_id = serializers.IntegerField()
    photo = serializers.ImageField()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_challenge_id(self, value):
        """Ensure challenge exists and is active"""
        try:
            Challenge.objects.get(id=value, is_active=True)
            return value
        except Challenge.DoesNotExist:
            raise serializers.ValidationError("Challenge not found or inactive")


class VerificationResultSerializer(serializers.Serializer):
    """Serializer for verification results"""

    success = serializers.BooleanField()
    message = serializers.CharField()
    attempt_id = serializers.IntegerField(required=False)
    points_earned = serializers.IntegerField(required=False)
    bonus_points = serializers.IntegerField(required=False)
    verification_details = serializers.DictField(required=False)
    quiz_generated = serializers.BooleanField(required=False)
    quiz_id = serializers.IntegerField(required=False)


class VerificationMetricsSerializer(serializers.ModelSerializer):
    challenge_title = serializers.CharField(source="challenge.title", read_only=True)
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = VerificationMetrics
        fields = [
            "challenge_title",
            "total_attempts",
            "successful_verifications",
            "failed_verifications",
            "success_rate",
            "average_verification_time",
            "photo_failures",
            "location_failures",
            "quality_failures",
            "last_updated",
        ]


class ChallengeStatsSerializer(serializers.Serializer):
    """Summary statistics for challenges"""

    total_challenges = serializers.IntegerField()
    completed_challenges = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_points_earned = serializers.IntegerField()
    favorite_location_type = serializers.CharField()
    recent_attempts = ChallengeAttemptSerializer(many=True)


class AdminVerificationSerializer(serializers.ModelSerializer):
    """Serializer for manual verification by admins"""

    class Meta:
        model = ChallengeAttempt
        fields = ["status", "verification_details", "points_earned", "bonus_points"]

    def validate_status(self, value):
        """Ensure valid status transition"""
        valid_statuses = ["verified", "failed", "rejected"]
        if value not in valid_statuses:
            raise serializers.ValidationError("Invalid status for manual verification")
        return value
